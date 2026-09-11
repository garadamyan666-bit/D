// Keep the existing widgets mounted so navigation never loses a market selection.
document.addEventListener('DOMContentLoaded', () => {
  const dictionary = {
    hy:['Վերլուծություն','Մակարդակներ և հիմնավորում','Շուկայի հոսք','Պատմական փորձարկում','Telegram ծանուցումներ','Շուկայի առաջատարներ','Պատմություն','Նկարի վերլուծություն','Իմ հաշիվը','Ադմին','Դուրս գալ','Ընտրեք շուկան և սեղմեք «Վերլուծել շուկան»։ Արդյունքը հասանելի կլինի նաև մյուս բաժիններում։','Վերևում ընտրեք շուկան և ժամանակահատվածը։','Binance բաժին․ տվյալները բեռնվում են Binance վերլուծություն կատարելուց հետո։','Բաժիններ'],
    ru:['Анализ','Уровни и обоснование','Поток рынка','Исторический тест','Уведомления Telegram','Лидеры рынка','История','Анализ изображения','Мой аккаунт','Админ','Выйти','Выберите рынок и нажмите «Анализировать рынок». Результат доступен и в других разделах.','Выберите выше рынок и таймфрейм.','Раздел Binance: данные загружаются после анализа Binance.','Разделы'],
    en:['Analysis','Levels and rationale','Market flow','Backtest','Telegram alerts','Market leaders','History','Chart image analysis','My account','Admin','Log out','Choose a market and select Analyze market. Results remain available across sections.','Select the market and timeframe above.','Binance section: data loads after running a Binance analysis.','Sections']
  };
  const main = document.querySelector('main');
  const menu = document.createElement('nav');menu.className='workspace-menu';
  main.before(menu);
  const heading=document.createElement('h2');heading.className='page-heading';heading.tabIndex=-1;
  const hint=document.createElement('p');hint.className='page-hint';
  const controls=main.querySelector('.controls');controls.before(heading,hint);
  const flow=main.querySelector('.intelligence-grid');
  const backtest=flow.lastElementChild;
  const groups=[['analysis',[main.querySelector('#signal'),main.querySelector('.metrics')]],['levels',[main.querySelector('.grid')]],['flow',[flow]],['backtest',[backtest]],['alerts',[main.querySelector('.alert-panel')]],['leaders',[main.querySelector('.market-leaders')]],['history',[main.querySelector('.recent')]],['chart',[main.querySelector('.chart-upload')]]];
  const panels=new Map();const links=[];
  for(const [key,widgets] of groups){
    const panel=document.createElement('section');panel.className='workspace-panel';panel.dataset.page=key;panel.id='page-'+key;panel.hidden=true;
    widgets.forEach(widget=>panel.append(widget));main.append(panel);panels.set(key,panel);
    const link=document.createElement('a');link.href='#'+key;link.setAttribute('aria-controls',panel.id);menu.append(link);links.push(link);
  }
  for(const url of ['/account','/admin']){const link=document.createElement('a');link.href=url;if(url==='/admin')link.hidden=true;menu.append(link);links.push(link);}
  const logout=document.createElement('a');logout.href='#logout';menu.append(logout);links.push(logout);
  fetch('/api/account').then(response=>response.json()).then(account=>{links[9].hidden=!account.is_admin;}).catch(()=>{});
  logout.addEventListener('click',async event=>{event.preventDefault();await fetch('/api/auth/logout',{method:'POST'});location.replace('/login');});
  let current='analysis';
  function render(){
    const lang=document.documentElement.lang;const words=dictionary[lang]||dictionary.hy;
    menu.setAttribute('aria-label',words[14]);links.forEach((link,i)=>{link.textContent=words[i];if(i<8&&groups[i][0]===current)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
    heading.textContent=words[groups.findIndex(([key])=>key===current)];
    hint.textContent=current==='alerts'?words[12]:['flow','backtest'].includes(current)?words[13]:['analysis','levels'].includes(current)?words[11]:'';
    hint.hidden=!hint.textContent;
  }
  function navigate(focus=false){
    const requested=location.hash.slice(1);current=panels.has(requested)?requested:'analysis';
    panels.forEach((panel,key)=>panel.hidden=key!==current);
    controls.hidden=['leaders','history','chart'].includes(current);
    render();
    if(focus){heading.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
  }
  window.addEventListener('hashchange',()=>navigate(true));
  new MutationObserver(render).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
  navigate();
});
