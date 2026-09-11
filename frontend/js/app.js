const $ = id => document.getElementById(id);

const translations = {
  hy: {
    brandEyebrow: 'ՇՈՒԿԱՅԻ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ', brandTitle: 'Առևտրի վերլուծության բոտ', checking: '● Կապի ստուգում',
    safety: 'ՄԻԱՅՆ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ — ԱՎՏՈՄԱՏ ԳՈՐԾԱՐՔՆԵՐ ՉԿԱՆ', source: 'Տվյալների աղբյուր', market: 'Շուկա', timeframe: 'Ժամանակահատված', analyze: 'Վերլուծել շուկան',
    currentOutlook: 'ԸՆԹԱՑԻԿ ԿԱՆԽԱՏԵՍՈՒՄ', waiting: 'ՍՊԱՍՈՒՄ', chooseMarket: 'Սկսելու համար ընտրեք շուկան', confidence: 'վստահություն', confidenceTitle: 'Վստահություն',
    trend: 'Միտում', strengthEmpty: 'Ուժգնություն՝ —', strength: 'Ուժգնություն', momentum: 'Շարժման թափ', signalEmpty: 'Ազդանշան՝ —', signal: 'Ազդանշան', volatility: 'Տատանողականություն', volume: 'Ծավալ', volumeNote: '20 շրջանի միջինի համեմատ',
    structure: 'Շուկայի կառուցվածք', support: 'Աջակցություն', resistance: 'Դիմադրություն', setup: 'Առաջարկվող կարգավորումներ', entry: 'Մուտքի գին', stop: 'Կորուստի սահման (SL)', target: 'Շահույթի թիրախ (TP)', riskReward: 'Ռիսկ / եկամուտ', theoreticalRisk: 'Տեսական ռիսկ',
    rationale: 'Վերլուծության հիմնավորումներ', noAnalysis: 'Վերլուծություն դեռ չի կատարվել։', noConfirmations: 'Ուղղությունը հաստատող բավարար տվյալներ չկան։', recent: 'Վերջին վերլուծությունները', refresh: 'Թարմացվում է յուրաքանչյուր 30 վայրկյանը մեկ', time: 'Ժամանակ', price: 'Գին', noHistory: 'Պահպանված վերլուծություններ դեռ չկան։',
    connected: 'միացված', disconnected: 'անջատված', analyzing: 'Վերլուծվում են {source}-ի իրական տվյալները…', invalidResponse: 'Սերվերը սխալ պատասխան է վերադարձրել', requestFailed: 'Հարցումը ձախողվեց'
  },
  ru: {
    brandEyebrow: 'АНАЛИТИКА РЫНКА', brandTitle: 'Бот анализа торговли', checking: '● Проверка соединения',
    safety: 'ТОЛЬКО АНАЛИЗ — БЕЗ АВТОМАТИЧЕСКИХ СДЕЛОК', source: 'Источник данных', market: 'Рынок', timeframe: 'Таймфрейм', analyze: 'Анализировать рынок',
    currentOutlook: 'ТЕКУЩИЙ ПРОГНОЗ', waiting: 'ОЖИДАНИЕ', chooseMarket: 'Выберите рынок, чтобы начать', confidence: 'уверенность', confidenceTitle: 'Уверенность',
    trend: 'Тренд', strengthEmpty: 'Сила: —', strength: 'Сила', momentum: 'Импульс', signalEmpty: 'Сигнал: —', signal: 'Сигнал', volatility: 'Волатильность', volume: 'Объём', volumeNote: 'в сравнении со средним за 20 периодов',
    structure: 'Структура рынка', support: 'Поддержка', resistance: 'Сопротивление', setup: 'Предлагаемые уровни', entry: 'Цена входа', stop: 'Стоп-лосс (SL)', target: 'Тейк-профит (TP)', riskReward: 'Риск / прибыль', theoreticalRisk: 'Теоретический риск',
    rationale: 'Обоснование анализа', noAnalysis: 'Анализ ещё не выполнен.', noConfirmations: 'Недостаточно подтверждений направления.', recent: 'Последние анализы', refresh: 'Обновляется каждые 30 секунд', time: 'Время', price: 'Цена', noHistory: 'Сохранённых анализов пока нет.',
    connected: 'подключён', disconnected: 'отключён', analyzing: 'Анализ реальных данных {source}…', invalidResponse: 'Сервер вернул некорректный ответ', requestFailed: 'Запрос не выполнен'
  },
  en: {
    brandEyebrow: 'MARKET INTELLIGENCE', brandTitle: 'Trade Analysis Bot', checking: '● Checking connections',
    safety: 'ANALYSIS ONLY — NO AUTOMATIC TRADE', source: 'Data source', market: 'Market', timeframe: 'Timeframe', analyze: 'Analyze market',
    currentOutlook: 'CURRENT OUTLOOK', waiting: 'WAITING', chooseMarket: 'Choose a market to begin', confidence: 'confidence', confidenceTitle: 'Confidence',
    trend: 'Trend', strengthEmpty: 'Strength —', strength: 'Strength', momentum: 'Momentum', signalEmpty: 'Signal —', signal: 'Signal', volatility: 'Volatility', volume: 'Volume', volumeNote: 'vs 20-period mean',
    structure: 'Market structure', support: 'Support', resistance: 'Resistance', setup: 'Suggested setup', entry: 'Entry', stop: 'Stop loss (SL)', target: 'Take profit (TP)', riskReward: 'Risk / reward', theoreticalRisk: 'Theoretical risk',
    rationale: 'Analysis rationale', noAnalysis: 'No analysis loaded.', noConfirmations: 'No sufficient directional confirmations.', recent: 'Recent analyses', refresh: 'Auto-refreshes every 30 seconds', time: 'Time', price: 'Price', noHistory: 'No analyses stored yet.',
    connected: 'connected', disconnected: 'offline', analyzing: 'Analyzing live {source} data…', invalidResponse: 'Invalid server response', requestFailed: 'Request failed'
  }
};

Object.assign(translations.hy, {
  marketFlow:'Շուկայի հոսք և խորություն', change24h:'24ժ փոփոխություն', volume24h:'24ժ շրջանառություն', trades24h:'24ժ գործարքների քանակ', spread:'Bid/Ask spread',
  buySellPressure:'Գնման / վաճառքի ճնշում', orderImbalance:'Order book անհավասարակշռություն', bookPressure:'Order book ուղղություն', takerRatio:'Ագրեսիվ գնումների բաժին', flowPressure:'Trade flow ուղղություն', aggregateNote:'Տվյալները ընդհանուր շուկայական հոսք են, ոչ թե գնորդների ինքնություն։',
  multiTimeframe:'Մի քանի ժամանակահատվածի համընկնում', backtest:'Պատմական փորձարկում', testedTrades:'Փորձարկված ազդանշաններ', winRate:'Հաղթող տոկոս', expectancy:'Միջին արդյունք (R)', maxDrawdown:'Առավելագույն անկում (R)', hypotheticalNote:'Backtest-ը ենթադրական է և ապագա արդյունք չի երաշխավորում։',
  marketLeaders:'Binance շուկայի առաջատարներ', leadersNote:'USDT զույգեր՝ նվազագույն շրջանառության զտիչով', topVolume:'Ամենաշատ շրջանառվող', topGainers:'Ամենաշատ աճող', topLosers:'Ամենաշատ նվազող', score:'միավոր',
  alertsTitle:'Telegram ազդանշաններ', alertIntro:'Ստացեք հաղորդագրություն, երբ ընտրված կանխատեսման confidence-ը հասնի ձեր շեմին։', telegramLanguage:'Telegram-ի լեզու', threshold:'Ծանուցման շեմ (%)', enableAlert:'Միացնել ընտրվածի ծանուցումը', testTelegram:'Փորձարկել Telegram-ը', telegramReady:'Telegram-ը միացված է', telegramMissing:'Telegram-ը դեռ կարգավորված չէ', noAlerts:'Ակտիվ ծանուցումներ դեռ չկան։', remove:'Ջնջել', alertSaved:'Ծանուցումը պահպանված է։', languageSaved:'Telegram-ի լեզուն պահպանված է։', testSent:'Փորձնական հաղորդագրությունն ուղարկված է։', checksEvery:'Ստուգում՝ յուրաքանչյուր {minutes} րոպեն մեկ', lastResult:'Վերջին արդյունք', notChecked:'դեռ չի ստուգվել', confidenceNotice:'Confidence-ը մոդելի համաձայնության չափն է, ոչ շահույթի հավանականություն կամ երաշխիք։'
});
Object.assign(translations.ru, {
  marketFlow:'Поток и глубина рынка', change24h:'Изменение за 24ч', volume24h:'Оборот за 24ч', trades24h:'Сделок за 24ч', spread:'Спред Bid/Ask',
  buySellPressure:'Давление покупки / продажи', orderImbalance:'Дисбаланс книги заявок', bookPressure:'Направление книги заявок', takerRatio:'Доля агрессивных покупок', flowPressure:'Направление потока сделок', aggregateNote:'Это совокупный рыночный поток, а не личности покупателей.',
  multiTimeframe:'Согласованность таймфреймов', backtest:'Исторический тест', testedTrades:'Протестировано сигналов', winRate:'Доля прибыльных', expectancy:'Средний результат (R)', maxDrawdown:'Максимальная просадка (R)', hypotheticalNote:'Backtest является гипотетическим и не гарантирует будущий результат.',
  marketLeaders:'Лидеры рынка Binance', leadersNote:'Пары USDT с фильтром минимального оборота', topVolume:'Наибольший оборот', topGainers:'Наибольший рост', topLosers:'Наибольшее падение', score:'баллов',
  alertsTitle:'Сигналы Telegram', alertIntro:'Получайте сообщение, когда confidence выбранного прогноза достигнет заданного порога.', telegramLanguage:'Язык Telegram', threshold:'Порог уведомления (%)', enableAlert:'Включить уведомление', testTelegram:'Проверить Telegram', telegramReady:'Telegram подключён', telegramMissing:'Telegram ещё не настроен', noAlerts:'Активных уведомлений пока нет.', remove:'Удалить', alertSaved:'Уведомление сохранено.', languageSaved:'Язык Telegram сохранён.', testSent:'Тестовое сообщение отправлено.', checksEvery:'Проверка каждые {minutes} мин.', lastResult:'Последний результат', notChecked:'ещё не проверялось', confidenceNotice:'Confidence — мера согласованности модели, а не вероятность или гарантия прибыли.'
});
Object.assign(translations.en, {
  marketFlow:'Market flow and depth', change24h:'24h change', volume24h:'24h turnover', trades24h:'24h trade count', spread:'Bid/Ask spread',
  buySellPressure:'Buy / sell pressure', orderImbalance:'Order-book imbalance', bookPressure:'Order-book direction', takerRatio:'Aggressive buy share', flowPressure:'Trade-flow direction', aggregateNote:'This is aggregate market flow, not buyer identity.',
  multiTimeframe:'Multi-timeframe consensus', backtest:'Historical backtest', testedTrades:'Tested signals', winRate:'Win rate', expectancy:'Average result (R)', maxDrawdown:'Maximum drawdown (R)', hypotheticalNote:'Backtesting is hypothetical and does not guarantee future results.',
  marketLeaders:'Binance market leaders', leadersNote:'USDT pairs with a minimum-turnover filter', topVolume:'Highest turnover', topGainers:'Top gainers', topLosers:'Top losers', score:'score',
  alertsTitle:'Telegram alerts', alertIntro:'Receive a message when the selected forecast confidence reaches your threshold.', telegramLanguage:'Telegram language', threshold:'Notification threshold (%)', enableAlert:'Enable selected alert', testTelegram:'Test Telegram', telegramReady:'Telegram connected', telegramMissing:'Telegram is not configured yet', noAlerts:'No active alerts yet.', remove:'Remove', alertSaved:'Alert saved.', languageSaved:'Telegram language saved.', testSent:'Test message sent.', checksEvery:'Checks every {minutes} min.', lastResult:'Last result', notChecked:'not checked yet', confidenceNotice:'Confidence measures model agreement; it is not a profit probability or guarantee.'
});

const signalLabels = {
  hy: {'STRONG BUY':'ՈՒԺԵՂ ԳՆՈՒՄ', BUY:'ԳՆԵԼ', WAIT:'ՍՊԱՍԵԼ', SELL:'ՎԱՃԱՌԵԼ', 'STRONG SELL':'ՈՒԺԵՂ ՎԱՃԱՌՔ'},
  ru: {'STRONG BUY':'СИЛЬНАЯ ПОКУПКА', BUY:'ПОКУПАТЬ', WAIT:'ЖДАТЬ', SELL:'ПРОДАВАТЬ', 'STRONG SELL':'СИЛЬНАЯ ПРОДАЖА'},
  en: {'STRONG BUY':'STRONG BUY', BUY:'BUY', WAIT:'WAIT', SELL:'SELL', 'STRONG SELL':'STRONG SELL'}
};
const trendLabels = {
  hy: {BULLISH:'ԱՃՈՂ', BEARISH:'ՆՎԱԶՈՂ', NEUTRAL:'ՉԵԶՈՔ'},
  ru: {BULLISH:'ВОСХОДЯЩИЙ', BEARISH:'НИСХОДЯЩИЙ', NEUTRAL:'НЕЙТРАЛЬНЫЙ'},
  en: {BULLISH:'BULLISH', BEARISH:'BEARISH', NEUTRAL:'NEUTRAL'}
};
const volumeLabels = {
  hy: {STRONG:'ՈՒԺԵՂ', 'NORMAL/WEAK':'ՍՈՎՈՐԱԿԱՆ / ԹՈՒՅԼ'},
  ru: {STRONG:'СИЛЬНЫЙ', 'NORMAL/WEAK':'ОБЫЧНЫЙ / СЛАБЫЙ'},
  en: {STRONG:'STRONG', 'NORMAL/WEAK':'NORMAL / WEAK'}
};
const pressureLabels = {
  hy: {BUY:'ԳՆՄԱՆ', SELL:'ՎԱՃԱՌՔԻ', BALANCED:'ՀԱՎԱՍԱՐԱԿՇՌՎԱԾ', MIXED:'ԽԱՌԸ'},
  ru: {BUY:'ПОКУПКА', SELL:'ПРОДАЖА', BALANCED:'БАЛАНС', MIXED:'СМЕШАННЫЙ'},
  en: {BUY:'BUY', SELL:'SELL', BALANCED:'BALANCED', MIXED:'MIXED'}
};
const phraseLabels = {
  hy: {
    'Bullish multi-EMA trend':'Աճող բազմակի EMA միտում', 'Bearish multi-EMA trend':'Նվազող բազմակի EMA միտում',
    'EMA20 is above EMA50':'EMA20-ը EMA50-ից բարձր է', 'EMA20 is below EMA50':'EMA20-ը EMA50-ից ցածր է',
    'MACD momentum is bullish':'MACD շարժման թափը աճող է', 'MACD momentum is bearish':'MACD շարժման թափը նվազող է',
    'Above-average tick volume confirms direction':'Միջինից բարձր tick ծավալը հաստատում է ուղղությունը',
    'Bullish price-action pattern':'Գնային շարժման աճող պատկեր', 'Bearish price-action pattern':'Գնային շարժման նվազող պատկեր',
    'Nearby support favors the long setup':'Մոտակա աջակցությունը նպաստում է գնման սցենարին', 'Nearby resistance favors the short setup':'Մոտակա դիմադրությունը նպաստում է վաճառքի սցենարին',
    'RSI is oversold; reversal is not guaranteed':'RSI-ն գերվաճառված է, սակայն շրջադարձը երաշխավորված չէ', 'RSI is overbought; trend may persist':'RSI-ն գերգնված է, սակայն միտումը կարող է շարունակվել',
    'Tick volume is below confirmation threshold':'Tick ծավալը հաստատման շեմից ցածր է', 'Resistance is less than one ATR away':'Դիմադրությունը մեկ ATR-ից պակաս հեռավորության վրա է', 'Support is less than one ATR away':'Աջակցությունը մեկ ATR-ից պակաս հեռավորության վրա է'
  },
  ru: {
    'Bullish multi-EMA trend':'Восходящий тренд нескольких EMA', 'Bearish multi-EMA trend':'Нисходящий тренд нескольких EMA',
    'EMA20 is above EMA50':'EMA20 выше EMA50', 'EMA20 is below EMA50':'EMA20 ниже EMA50',
    'MACD momentum is bullish':'Импульс MACD восходящий', 'MACD momentum is bearish':'Импульс MACD нисходящий',
    'Above-average tick volume confirms direction':'Тиковый объём выше среднего подтверждает направление',
    'Bullish price-action pattern':'Бычья модель движения цены', 'Bearish price-action pattern':'Медвежья модель движения цены',
    'Nearby support favors the long setup':'Близкая поддержка благоприятна для покупки', 'Nearby resistance favors the short setup':'Близкое сопротивление благоприятно для продажи',
    'RSI is oversold; reversal is not guaranteed':'RSI в зоне перепроданности, но разворот не гарантирован', 'RSI is overbought; trend may persist':'RSI в зоне перекупленности, но тренд может продолжиться',
    'Tick volume is below confirmation threshold':'Тиковый объём ниже порога подтверждения', 'Resistance is less than one ATR away':'Сопротивление находится ближе одного ATR', 'Support is less than one ATR away':'Поддержка находится ближе одного ATR'
  },
  en: {}
};

let currentLang = localStorage.getItem('tradeBotLanguage') || 'hy';
if (!translations[currentLang]) currentLang = 'hy';
let sourceSymbols = {};
let lastAnalysis = null;
let historyRows = [];
let healthState = null;
let intelligenceState = null;
let backtestState = null;
let leadersState = null;
let alertStatusState = null;
let alertRows = [];

const t = key => translations[currentLang][key] || translations.en[key] || key;
const locale = () => ({hy:'hy-AM', ru:'ru-RU', en:'en-US'})[currentLang];
const number = value => value == null ? '—' : Number(value).toLocaleString(locale(), {maximumSignificantDigits: 7});
const compactNumber = value => value == null ? '—' : Number(value).toLocaleString(locale(), {notation:'compact', maximumFractionDigits:2});
const escapeHtml = value => { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; };
const cls = signal => signal.includes('BUY') ? 'buy' : signal.includes('SELL') ? 'sell' : 'neutral';
const translatePhrase = phrase => phraseLabels[currentLang][phrase] || phrase;

function renderHealth() {
  if (!healthState) return;
  $('status').textContent = `● Binance՝ ${healthState.binance_connected ? t('connected') + ' ✓' : t('disconnected') + ' ✕'}`;
  $('status').classList.toggle('on', healthState.binance_connected);
}

function applyLanguage() {
  document.documentElement.lang = currentLang;
  document.title = t('brandTitle');
  document.querySelectorAll('[data-i18n]').forEach(element => { element.textContent = t(element.dataset.i18n); });
  document.querySelectorAll('[data-lang]').forEach(button => {
    const active = button.dataset.lang === currentLang;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  renderHealth();
  if (lastAnalysis) renderAnalysis(lastAnalysis);
  if (intelligenceState) renderIntelligence(intelligenceState);
  if (backtestState) renderBacktest(backtestState);
  if (leadersState) renderLeaders(leadersState);
  renderAlerts();
  renderHistory();
}

async function json(url, options) {
  let response;
  try { response = await fetch(url, options); }
  catch { throw new Error(t('requestFailed')); }
  let body;
  try { body = await response.json(); }
  catch { body = {detail: t('invalidResponse')}; }
  if (response.status === 401) { location.replace('/login'); throw new Error(''); }
  if (!response.ok) throw new Error(body.detail || `${t('requestFailed')}: HTTP ${response.status}`);
  return body;
}

function fillSymbols() {
  const sourceSelect = $('source');
  const symbolSelect = $('symbol');
  if (!sourceSelect || !symbolSelect) return;
  symbolSelect.innerHTML = '';
  (sourceSymbols[sourceSelect.value] || []).forEach(symbol => symbolSelect.add(new Option(symbol, symbol)));
}

function put(id, value) { $(id).textContent = number(value); }

function renderAnalysis(analysis) {
  lastAnalysis = analysis;
  $('signal').className = `signal card ${cls(analysis.signal)}`;
  $('signalName').removeAttribute('data-i18n');
  $('stamp').removeAttribute('data-i18n');
  $('strength').removeAttribute('data-i18n');
  $('macdSignal').removeAttribute('data-i18n');
  $('signalName').textContent = signalLabels[currentLang][analysis.signal] || analysis.signal;
  $('confidence').textContent = `${analysis.confidence}%`;
  $('stamp').textContent = `BINANCE · ${analysis.symbol} · ${analysis.timeframe} · ${new Date(analysis.timestamp).toLocaleString(locale())}`;
  $('trend').textContent = trendLabels[currentLang][analysis.trend] || analysis.trend;
  $('strength').textContent = `${t('strength')}: ${analysis.trend_strength}%`;
  put('rsi', analysis.rsi); put('macd', analysis.macd); put('atr', analysis.atr);
  $('macdSignal').textContent = `${t('signal')}: ${number(analysis.macd_signal)}`;
  $('volume').textContent = volumeLabels[currentLang][analysis.volume_status] || analysis.volume_status;
  ['ema20','ema50','ema200','support','resistance','entry'].forEach(id => put(id, analysis[id]));
  put('stop', analysis.stop_loss); put('target', analysis.take_profit);
  $('rr').textContent = analysis.stop_loss ? `1 : ${analysis.risk_reward}` : '—';
  $('risk').textContent = analysis.risk ? `$${number(analysis.risk.risk_amount)}` : '—';
  $('reasons').innerHTML = (analysis.reasons || []).map(reason => `<li>${escapeHtml(translatePhrase(reason))}</li>`).join('') || `<li>${t('noConfirmations')}</li>`;
  $('warnings').textContent = (analysis.warnings || []).map(warning => `⚠ ${translatePhrase(warning)}`).join('\n');
}

function renderIntelligence(data) {
  intelligenceState = data;
  const change = Number(data.price_change_24h_pct);
  $('change24h').textContent = `${change >= 0 ? '+' : ''}${number(change)}%`;
  $('change24h').className = change >= 0 ? 'positive' : 'negative';
  $('volume24h').textContent = `$${compactNumber(data.quote_volume_24h)}`;
  $('trades24h').textContent = compactNumber(data.trade_count_24h);
  $('spread').textContent = `${number(data.spread_bps)} bps`;
  const imbalance = Number(data.order_book_imbalance_pct);
  $('orderImbalance').textContent = `${imbalance >= 0 ? '+' : ''}${number(imbalance)}%`;
  $('orderImbalance').className = imbalance >= 0 ? 'positive' : 'negative';
  $('bookPressure').textContent = pressureLabels[currentLang][data.order_book_pressure] || data.order_book_pressure;
  $('takerRatio').textContent = `${number(data.taker_buy_ratio_pct)}%`;
  $('flowPressure').textContent = pressureLabels[currentLang][data.trade_flow_pressure] || data.trade_flow_pressure;
  const consensus = data.multi_timeframe;
  $('consensus').textContent = pressureLabels[currentLang][consensus.consensus] || consensus.consensus;
  $('consensusScore').textContent = `${number(consensus.average_score)} ${t('score')}`;
  $('timeframeConsensus').innerHTML = consensus.timeframes.map(item => `<div class="timeframe-row"><strong>${escapeHtml(item.timeframe)}</strong><span class="tag ${cls(item.signal)}">${escapeHtml(signalLabels[currentLang][item.signal] || item.signal)}</span><span>${item.score}</span></div>`).join('');
}

function renderBacktest(data) {
  backtestState = data;
  $('testedTrades').textContent = number(data.trades);
  $('winRate').textContent = `${number(data.win_rate_pct)}%`;
  $('expectancy').textContent = number(data.expectancy_r);
  $('profitFactor').textContent = data.profit_factor == null ? '—' : number(data.profit_factor);
  $('maxDrawdown').textContent = number(data.max_drawdown_r);
}

function leaderRows(items, showVolume = false) {
  return items.map(item => {
    const change = Number(item.price_change_pct);
    const secondary = showVolume ? `$${compactNumber(item.quote_volume)}` : `${change >= 0 ? '+' : ''}${number(change)}%`;
    return `<div class="leader-row"><strong>${escapeHtml(item.symbol)}</strong><small>${number(item.last_price)}</small><span class="${change >= 0 ? 'positive' : 'negative'}">${secondary}</span></div>`;
  }).join('');
}

function renderLeaders(data) {
  leadersState = data;
  $('topVolume').innerHTML = leaderRows(data.top_volume, true);
  $('topGainers').innerHTML = leaderRows(data.top_gainers);
  $('topLosers').innerHTML = leaderRows(data.top_losers);
}

async function loadAdvanced(symbol, timeframe) {
  const [intelligence, backtest] = await Promise.allSettled([
    json(`/api/intelligence/binance/${encodeURIComponent(symbol)}`),
    json(`/api/backtest/binance/${encodeURIComponent(symbol)}/${encodeURIComponent(timeframe)}?horizon_bars=12&max_trades=60&cost_bps=10`)
  ]);
  if (intelligence.status === 'fulfilled') renderIntelligence(intelligence.value);
  if (backtest.status === 'fulfilled') renderBacktest(backtest.value);
  if (intelligence.status === 'rejected' && backtest.status === 'rejected') $('message').textContent = intelligence.reason.message;
}

async function loadLeaders() {
  try { renderLeaders(await json('/api/markets/binance/leaders?limit=8')); }
  catch (error) { console.error(error); }
}

function renderHistory() {
  const table = $('history');
  if (!table) return;
  table.innerHTML = historyRows.map(item => `<tr><td>${new Date(item.timestamp).toLocaleString(locale())}</td><td>BINANCE · ${escapeHtml(item.symbol)} ${escapeHtml(item.timeframe)}</td><td><span class="tag ${cls(item.signal)}">${escapeHtml(signalLabels[currentLang][item.signal] || item.signal)}</span></td><td>${item.confidence}%</td><td>${number(item.current_price)}</td></tr>`).join('') || `<tr><td colspan="5">${t('noHistory')}</td></tr>`;
}

async function loadHistory() {
  try { historyRows = await json('/api/signals?limit=20'); renderHistory(); }
  catch (error) { console.error(error); }
}

function renderAlerts() {
  if (!$('alertList')) return;
  if (alertStatusState) {
    $('telegramStatus').textContent = `${alertStatusState.telegram_configured ? '● ' + t('telegramReady') : '○ ' + t('telegramMissing')} · ${t('checksEvery').replace('{minutes}', alertStatusState.scan_interval_minutes)}`;
    $('telegramStatus').classList.toggle('ready', alertStatusState.telegram_configured);
    $('telegramLanguage').value = alertStatusState.language || 'hy';
  }
  $('alertList').innerHTML = alertRows.map(item => {
    const last = item.last_signal ? `${t('lastResult')}: ${signalLabels[currentLang][item.last_signal] || item.last_signal} · ${number(item.last_confidence)}%` : t('notChecked');
    return `<div class="alert-row"><div><strong>${escapeHtml(item.source)} · ${escapeHtml(item.symbol)} · ${escapeHtml(item.timeframe)} · ≥${number(item.min_confidence)}%</strong><small>${escapeHtml(last)}</small></div><button class="secondary remove-alert" data-alert-id="${item.id}">${t('remove')}</button></div>`;
  }).join('') || `<p class="empty-state">${t('noAlerts')}</p>`;
}

async function loadAlerts() {
  try {
    [alertStatusState, alertRows] = await Promise.all([json('/api/alerts/status'), json('/api/alerts')]);
    renderAlerts();
  } catch (error) { $('alertMessage').textContent = error.message; }
}

async function saveAlert() {
  const threshold = Number($('alertThreshold').value);
  $('alertMessage').textContent = '';
  try {
    await json('/api/alerts', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({source:$('source').value, symbol:$('symbol').value, timeframe:$('timeframe').value, min_confidence:threshold})});
    $('alertMessage').textContent = t('alertSaved');
    await loadAlerts();
  } catch (error) { $('alertMessage').textContent = error.message; }
}

async function testAlert() {
  $('alertMessage').textContent = '';
  try {
    await json('/api/alerts/test', {method:'POST'});
    $('alertMessage').textContent = t('testSent');
  } catch (error) { $('alertMessage').textContent = error.message; }
}

async function saveAlertLanguage() {
  try {
    const result = await json('/api/alerts/language', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({language:$('telegramLanguage').value})});
    if (alertStatusState) alertStatusState.language = result.language;
    $('alertMessage').textContent = t('languageSaved');
  } catch (error) { $('alertMessage').textContent = error.message; }
}

async function removeAlert(id) {
  try { await json(`/api/alerts/${id}`, {method:'DELETE'}); await loadAlerts(); }
  catch (error) { $('alertMessage').textContent = error.message; }
}

async function analyze() {
  const button = $('analyze');
  const source = $('source').value;
  button.disabled = true;
  $('message').textContent = t('analyzing').replace('{source}', source);
  try {
    const analysis = await json(`/api/analyze/${encodeURIComponent(source)}/${encodeURIComponent($('symbol').value)}/${encodeURIComponent($('timeframe').value)}`);
    renderAnalysis(analysis);
    $('message').textContent = '';
    if (source === 'BINANCE') await loadAdvanced(analysis.symbol, analysis.timeframe);
    await loadHistory();
    await loadAlerts();
  } catch (error) { $('message').textContent = error.message; }
  finally { button.disabled = false; }
}

async function boot() {
  applyLanguage();
  try {
    const [health, config, account] = await Promise.all([json('/api/health'), json('/api/symbols'), json('/api/account')]);
    currentLang = account.language || currentLang;
    localStorage.setItem('tradeBotLanguage', currentLang);
    applyLanguage();
    healthState = health;
    renderHealth();
    sourceSymbols = config.sources || {BINANCE: config.symbols};
    Object.keys(sourceSymbols).forEach(source => $('source').add(new Option(source, source)));
    fillSymbols();
    config.timeframes.forEach(timeframe => $('timeframe').add(new Option(timeframe, timeframe)));
    $('timeframe').value = config.default_timeframe;
    await loadHistory();
    await loadAlerts();
    if (sourceSymbols.BINANCE) loadLeaders();
  } catch (error) { $('message').textContent = error.message; }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-lang]').forEach(button => button.addEventListener('click', () => {
    currentLang = button.dataset.lang;
    localStorage.setItem('tradeBotLanguage', currentLang);
    applyLanguage();
  }));
  $('source').addEventListener('change', fillSymbols);
  $('analyze').addEventListener('click', analyze);
  $('saveAlert').addEventListener('click', saveAlert);
  $('testAlert').addEventListener('click', testAlert);
  $('telegramLanguage').addEventListener('change', saveAlertLanguage);
  $('alertList').addEventListener('click', event => {
    const button = event.target.closest('.remove-alert');
    if (button) removeAlert(button.dataset.alertId);
  });
  boot();
  setInterval(loadHistory, 30000);
});
