/* BRVM Dashboard JS - externalized */
/* global Chart */

function initBrvmDashboard(opts) {
	const { urls } = opts;

	const fmtK = (n)=> n==null? '--' : (Math.abs(n)>=1000? (n/1000).toFixed(2)+' K' : Number(n).toLocaleString());
	const fmtPct = (n)=> n==null? '--' : (n>=0? '+' : '') + Number(n).toFixed(2) + ' %';

	let candleChart;
	let currentPeriod = '';
	let sortMode = 'symbol'; // 'symbol' | 'change'

	function setLoading(state){
		const root = document.getElementById('sparklines');
		if(!root) return;
		root.style.opacity = state ? 0.5 : 1;
	}

	function currentPeriodQuery(prefix='?'){
		if(!currentPeriod) return '';
		return prefix + 'period=' + encodeURIComponent(currentPeriod);
	}

	async function loadSummary(){
		const res = await fetch(urls.summary + currentPeriodQuery());
		const data = await res.json();
		const lastUpdate = document.getElementById('brvm-last-update');
		if(lastUpdate) lastUpdate.textContent = data.last_update || '--';
		const refreshTs = document.getElementById('brvm-refresh-ts');
		if(refreshTs) refreshTs.textContent = new Date().toLocaleTimeString();
		if(data.indices){
			const v10 = document.getElementById('brvm10-value');
			const c10 = document.getElementById('brvm10-change');
			const vco = document.getElementById('compo-value');
			const cco = document.getElementById('compo-change');
			if(v10) v10.textContent = data.indices.brvm10?.value ?? '--';
			if(c10) c10.textContent = data.indices.brvm10? ' ' + fmtPct(data.indices.brvm10.change_pct): '';
			if(vco) vco.textContent = data.indices.composite?.value ?? '--';
			if(cco) cco.textContent = data.indices.composite? ' ' + fmtPct(data.indices.composite.change_pct): '';
		}
		if(data.kpis){
			const traded = document.getElementById('kpi-traded');
			const cap = document.getElementById('kpi-cap');
			const sector = document.getElementById('kpi-sector');
			if(traded) traded.textContent = fmtK(data.kpis.traded_value);
			if(cap) cap.textContent = fmtK(data.kpis.capitalization);
			if(sector) sector.textContent = fmtPct(data.kpis.sector_avg_change);
		}
	}

	async function loadSparklines(){
		setLoading(true);
		const res = await fetch(urls.stocks + '?points=30' + currentPeriodQuery('&'));
		const data = await res.json();
		const container = document.getElementById('sparklines');
		const select = document.getElementById('symbol-select');
		if(!container || !select) return;
		container.innerHTML = '';
		select.innerHTML = '';
		let items = data.items || [];
		if(sortMode === 'change'){
			items = items.sort((a,b)=> (b.change_pct||0) - (a.change_pct||0));
		} else {
			items = items.sort((a,b)=> String(a.symbol).localeCompare(String(b.symbol)));
		}
		items.slice(0,8).forEach(item=>{
			const card = document.createElement('div');
			card.className = 'card-dark';
			card.style.padding = '.75rem';
			card.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;">
				<strong>${item.symbol}</strong>
				<span class="${item.change_pct>=0? 'accent' : ''}">${fmtPct(item.change_pct)}</span>
			</div>
			<canvas height="60"></canvas>`;
			container.appendChild(card);
			const ctx = card.querySelector('canvas').getContext('2d');
			new Chart(ctx, { type:'line', data:{ labels: item.series.map((_,i)=>i), datasets:[{ data:item.series, borderColor:'#C9A961', borderWidth:1, pointRadius:0, fill:false, tension:0.3 }] }, options:{ plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:false}} } });
		});
		items.forEach(i=>{ const opt=document.createElement('option'); opt.value=i.symbol; opt.textContent=i.symbol; select.appendChild(opt); });
		if(select.options.length>0){ loadCandles(select.value); }
		select.onchange = ()=> loadCandles(select.value);
		setLoading(false);
	}

	async function loadCandles(symbol){
		const res = await fetch(urls.candles + '?symbol=' + encodeURIComponent(symbol) + currentPeriodQuery('&'));
		const data = await res.json();
		const points = (data.candles||[]).map(c=> ({ x: new Date(c.ts), o: c.open, h: c.high, l: c.low, c: c.close }));
		const ctx = document.getElementById('candles').getContext('2d');
		if(candleChart) candleChart.destroy();
		candleChart = new Chart(ctx, {
			type: 'candlestick',
			data: { datasets: [{ label: symbol + ' (OHLC)', data: points, borderColor:'#C9A961', upColor:'#16A34A', downColor:'#DC2626', color:'#C9A961' }] },
			options: {
				responsive:true,
				maintainAspectRatio:false,
				plugins:{ legend:{ labels:{ color:'#E6E6E6' } } },
				scales:{
					x:{ type:'time', adapters:{ date: {} }, ticks:{ color:'#64748B' }, grid:{ display:false }},
					y:{ ticks:{ color:'#64748B' }, grid:{ color:'#1E293B' } }
				}
			}
		});
	}

	async function loadWinnersLosers(){
		const res = await fetch(urls.winnersLosers + currentPeriodQuery());
		const data = await res.json();
		const w = document.getElementById('winners');
		const l = document.getElementById('losers');
		if(!w || !l) return;
		function build(list, positive){
			return (list||[]).map(it=> `<div style="display:flex;justify-content:space-between;margin:.25rem 0;">
				<span>${it.symbol}</span><strong style="color:${positive?'#16A34A':'#DC2626'}">${fmtPct(it.change_pct)}</strong>
			</div>`).join('');
		}
		w.innerHTML = build(data.winners, true);
		l.innerHTML = build(data.losers, false);
	}

	async function refresh(){
		await loadSummary();
		await loadSparklines();
		await loadWinnersLosers();
	}

	// Wire period buttons and sort buttons
	document.querySelectorAll('.period-btn').forEach(btn=>{
		btn.addEventListener('click', ()=>{
			document.querySelectorAll('.period-btn').forEach(b=> b.classList.remove('active'));
			btn.classList.add('active');
			currentPeriod = btn.dataset.period || '';
			refresh();
		});
	});
	document.querySelectorAll('.sort-btn').forEach(btn=>{
		btn.addEventListener('click', ()=>{
			document.querySelectorAll('.sort-btn').forEach(b=> b.classList.remove('active'));
			btn.classList.add('active');
			sortMode = btn.dataset.sort || 'symbol';
			loadSparklines();
		});
	});

	refresh();
	setInterval(refresh, 30000);
}

// UMD fallback (if not using modules)
if (typeof window !== 'undefined') {
	window.BrvmDashboard = { initBrvmDashboard };
}