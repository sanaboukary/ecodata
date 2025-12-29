/* WorldBank Dashboard JS */
/* global Chart */

function initWorldBankDashboard(opts) {
	const { urls } = opts;

	const fmtK = (n)=> n==null? '--' : (Math.abs(n)>=1000? (n/1000).toFixed(2)+' K' : Number(n).toLocaleString());
	const fmtPct = (n)=> n==null? '--' : (n>=0? '+' : '') + Number(n).toFixed(2) + ' %';

	let radarChart;
	let currentPeriod = '';
	let currentCountry = '';

	function currentQuery(prefix='?'){
		const params = [];
		if(currentPeriod) params.push('period=' + encodeURIComponent(currentPeriod));
		if(currentCountry) params.push('country=' + encodeURIComponent(currentCountry));
		return params.length? prefix + params.join('&') : '';
	}

	async function loadCountries(){
		const res = await fetch(urls.countries);
		const data = await res.json();
		const select = document.getElementById('country-select');
		if(!select) return;
		data.countries.forEach(c=>{
			const opt = document.createElement('option');
			opt.value = c.name;
			opt.textContent = c.name + ' (' + c.count + ')';
			select.appendChild(opt);
		});
		select.onchange = ()=> {
			currentCountry = select.value;
			refresh();
		};
	}

	async function loadSummary(){
		const res = await fetch(urls.summary + currentQuery());
		const data = await res.json();
		const lastUpdate = document.getElementById('wb-last-update');
		if(lastUpdate) lastUpdate.textContent = data.last_update || '--';
		const refreshTs = document.getElementById('wb-refresh-ts');
		if(refreshTs) refreshTs.textContent = new Date().toLocaleTimeString();
		if(data.kpis){
			const gdp = document.getElementById('kpi-gdp-growth');
			const pov = document.getElementById('kpi-poverty');
			const gni = document.getElementById('kpi-gni');
			const spending = document.getElementById('kpi-spending');
			if(gdp) gdp.textContent = data.kpis.gdp_growth_pct!=null? fmtPct(data.kpis.gdp_growth_pct) : '--';
			if(pov) pov.textContent = data.kpis.poverty_rate!=null? '$'+data.kpis.poverty_rate : '--';
			if(gni) gni.textContent = data.kpis.gni_per_capita!=null? '$'+data.kpis.gni_per_capita : '--';
			if(spending) spending.textContent = data.kpis.public_spending_pct!=null? data.kpis.public_spending_pct+'%' : '--';
			// Doing Business radar
			const db = data.kpis.doing_business || {};
			updateRadar(db);
			updateProgressBars(db);
		}
	}

	function updateRadar(db){
		const ctx = document.getElementById('radar-chart');
		if(!ctx) return;
		if(radarChart) radarChart.destroy();
		radarChart = new Chart(ctx, {
			type: 'radar',
			data: {
				labels: ['Voix', 'Vide loi', 'Stabilité', 'Corruption', 'Éducation', 'Efficacité'],
				datasets: [{
					label: 'Doing Business',
					data: [db.voice||0, db.rule_of_law||0, db.political_stability||0, db.corruption_control||0, db.educational_effectiveness||0, db.efficiency||0],
					borderColor: '#4A9EFF',
					backgroundColor: 'rgba(74,158,255,0.2)',
					borderWidth: 2,
					pointBackgroundColor: '#4A9EFF'
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins:{ legend:{ display: false }},
				scales: { r: { min: 0, max: 100, ticks:{ color:'#64748B' }, grid:{ color:'#1E293B' }, pointLabels:{ color:'#94A3B8', font:{size:10} }} }
			}
		});
	}

	function updateProgressBars(db){
		document.getElementById('db-voice').textContent = (db.voice||0) + '%';
		document.getElementById('db-voice-bar').style.width = (db.voice||0) + '%';
		document.getElementById('db-rule').textContent = (db.rule_of_law||0) + '%';
		document.getElementById('db-rule-bar').style.width = (db.rule_of_law||0) + '%';
		document.getElementById('db-stability').textContent = (db.political_stability||0) + '%';
		document.getElementById('db-stability-bar').style.width = (db.political_stability||0) + '%';
		document.getElementById('db-corruption').textContent = (db.corruption_control||0) + '%';
		document.getElementById('db-corruption-bar').style.width = (db.corruption_control||0) + '%';
		document.getElementById('db-education').textContent = (db.educational_effectiveness||0) + '%';
		document.getElementById('db-education-bar').style.width = (db.educational_effectiveness||0) + '%';
		document.getElementById('db-efficiency').textContent = (db.efficiency||0) + '%';
		document.getElementById('db-efficiency-bar').style.width = (db.efficiency||0) + '%';
	}

	async function loadIndicators(){
		const res = await fetch(urls.indicators + '?points=20' + currentQuery('&'));
		const data = await res.json();
		const container = document.getElementById('indicators-sparklines');
		if(!container) return;
		container.innerHTML = '';
		(data.items||[]).slice(0,4).forEach(item=>{
			const card = document.createElement('div');
			card.style.cssText = 'padding:.5rem; background:#0B0F14; border:1px solid #1E293B; border-radius:6px;';
			const change_color = (item.change_pct||0) >= 0? '#16A34A' : '#DC2626';
			card.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.25rem;">
				<span style="font-size:.65rem; color:#94A3B8;">${item.indicator}</span>
				<span style="font-size:.7rem; color:${change_color};">${fmtPct(item.change_pct)}</span>
			</div>
			<canvas height="30"></canvas>`;
			container.appendChild(card);
			const ctx = card.querySelector('canvas').getContext('2d');
			new Chart(ctx, { type:'line', data:{ labels: item.series.map((_,i)=>i), datasets:[{ data:item.series, borderColor:'#4A9EFF', borderWidth:1, pointRadius:0, fill:false, tension:0.3 }] }, options:{ plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:false}} } });
		});
	}

	async function loadSectors(){
		const res = await fetch(urls.sectors + currentQuery());
		const data = await res.json();
		const sectors = data.sectors || {};
		
		// Education
		if(sectors.education){
			const e = sectors.education;
			const setPct = (id, val, changeId, change) => {
				const el = document.getElementById(id);
				const chEl = document.getElementById(changeId);
				if(el) el.textContent = val!=null? val.toFixed(1)+'%' : '--';
				if(chEl) chEl.textContent = change!=null? fmtPct(change) : '--';
			};
			setPct('edu-primary', e.primary_enrollment?.value, 'edu-primary-change', e.primary_enrollment?.change_pct);
			setPct('edu-secondary', e.secondary_enrollment?.value, 'edu-secondary-change', e.secondary_enrollment?.change_pct);
			setPct('edu-literacy', e.literacy_rate?.value, 'edu-literacy-change', e.literacy_rate?.change_pct);
			setPct('edu-spending', e.education_spending?.value, 'edu-spending-change', e.education_spending?.change_pct);
		}
		
		// Health
		if(sectors.health){
			const h = sectors.health;
			const setHealth = (id, val, changeId, change, suffix='') => {
				const el = document.getElementById(id);
				const chEl = document.getElementById(changeId);
				if(el) el.textContent = val!=null? val.toFixed(1)+suffix : '--';
				if(chEl) chEl.textContent = change!=null? fmtPct(change) : '--';
			};
			setHealth('health-life', h.life_expectancy?.value, 'health-life-change', h.life_expectancy?.change_pct);
			setHealth('health-spending', h.health_spending?.value, 'health-spending-change', h.health_spending?.change_pct, '%');
			setHealth('health-doctors', h.doctors_per_1000?.value, 'health-doctors-change', h.doctors_per_1000?.change_pct);
			setHealth('health-mortality', h.maternal_mortality?.value, 'health-mortality-change', h.maternal_mortality?.change_pct);
		}
		
		// Infrastructure
		if(sectors.infrastructure){
			const i = sectors.infrastructure;
			const setInfra = (id, val, changeId, change, barId, suffix='') => {
				const el = document.getElementById(id);
				const chEl = document.getElementById(changeId);
				const barEl = document.getElementById(barId);
				if(el) el.textContent = val!=null? val.toFixed(1)+suffix : '--';
				if(chEl) chEl.textContent = change!=null? fmtPct(change) : '--';
				if(barEl) barEl.style.width = (val!=null? val : 0) + '%';
			};
			setInfra('infra-electricity', i.electricity_access?.value, 'infra-electricity-change', i.electricity_access?.change_pct, 'infra-electricity-bar', '%');
			setInfra('infra-internet', i.internet_users?.value, 'infra-internet-change', i.internet_users?.change_pct, 'infra-internet-bar', '%');
			setInfra('infra-water', i.water_access?.value, 'infra-water-change', i.water_access?.change_pct, 'infra-water-bar', '%');
			
			const mobEl = document.getElementById('infra-mobile');
			const mobChEl = document.getElementById('infra-mobile-change');
			if(mobEl) mobEl.textContent = i.mobile_subscriptions?.value!=null? i.mobile_subscriptions.value.toFixed(1) : '--';
			if(mobChEl) mobChEl.textContent = i.mobile_subscriptions?.change_pct!=null? fmtPct(i.mobile_subscriptions.change_pct) : '--';
		}
	}

	async function refresh(){
		await loadSummary();
		await loadIndicators();
		await loadSectors();
	}

	// Wire period buttons
	document.querySelectorAll('.period-btn').forEach(btn=>{
		btn.addEventListener('click', ()=>{
			document.querySelectorAll('.period-btn').forEach(b=> b.classList.remove('active'));
			btn.classList.add('active');
			currentPeriod = btn.dataset.period || '';
			refresh();
		});
	});

	loadCountries();
	refresh();
	setInterval(refresh, 30000);
}

// UMD fallback
if (typeof window !== 'undefined') {
	window.WorldBankDashboard = { initWorldBankDashboard };
}
