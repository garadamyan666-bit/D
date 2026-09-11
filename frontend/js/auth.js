const form=document.getElementById('form');
form.addEventListener('submit',async event=>{event.preventDefault();const register=form.dataset.register==='true';const error=document.getElementById('error');error.textContent='';
 if(register&&form.elements.password.value!==form.elements.confirm.value){error.textContent='Գաղտնաբառերը չեն համընկնում։';return;}
 const button=form.querySelector('button');button.disabled=true;
 try{const response=await fetch(register?'/api/auth/register':'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:form.elements.username.value,password:form.elements.password.value})});const body=await response.json();if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:'Գործողությունը չստացվեց։');
 const requested=new URLSearchParams(location.search).get('next');location.replace(requested&&requested.startsWith('/')&&!requested.startsWith('//')?requested:'/');
 }catch(reason){error.textContent=reason.message;}finally{button.disabled=false;}});
