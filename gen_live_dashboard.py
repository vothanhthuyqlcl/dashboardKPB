import json

with open('/home/claude/node_modules/chart.js/dist/chart.umd.min.js', encoding='utf-8') as f:
    chartjs_code = f.read()

SHEET_ID = "1skBcfE9mumRyYB8xjWFZQrTjOt2afoAzVrJw13KQAQI"
CSV_URL_DETAIL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=680153173"
CSV_URL_AGGREGATE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=1124933797"
CSV_URL_VIOLATIONS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=2023013268"

APP_JS = r"""
// ============ CẤU HÌNH ============
const TARGETS = {nhandang:0.85, vongtay:1.0, tenga:0.95, atpt:0.85, "5s":0.80};
const SECTION_TITLES = {
  nhandang:"Nhận dạng người bệnh",
  vongtay:"Vòng tay nhận dạng",
  tenga:"Đánh giá & phòng\u00A0ngừa\u00A0té\u00A0ngã",
  atpt:"Thực hành bảng kiểm ATPT",
  "5s":"Thực hiện 5S"
};
const SECTION_COLORS = {
  nhandang:"#3B6FA8", vongtay:"#4C9F70", tenga:"#E0812F", atpt:"#8B5FBF", "5s":"#B08642"
};
const ALERT = "#D64550";
const TARGET_LINE = "#33475B";
const INK = "#1F2E3D";
const ATPT_ELIGIBLE = new Set(["A2.b","A14","A16","B1.a","B1.b","B1.c","B1.d","B1.e","B2","B3","B4","B6","B7","B8","B9","B11"]);
const NHANDANG_MSYT_ONLY = new Set(["A12","B12"]);
const MONTH_LABELS = ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12'];

// Cột số lượng mẫu đã giám sát (để hiện "đã giám sát N hồ sơ/NB")
const SAMPLE_COL = {nhandang:5, vongtay:13, tenga:21, atpt:29, "5s":43}; // ND_SOTH, VT_SONB, TN_TONGPHIEU, ATPT_SOHOSO, S5_SOKHUVUC
const SAMPLE_UNIT_LABEL = {nhandang:"hồ sơ", vongtay:"người bệnh", tenga:"phiếu", atpt:"hồ sơ", "5s":"khu vực"};

// 4 mức cảnh báo theo mức thiếu hụt so với mục tiêu
const TIER_COLORS = {good:"#1E8A57", yellow:"#D9A441", orange:"#E07A2C", red:"#B8402A", na:"#C7D2DA"};
function tierOf(value, target){
  if(value===null || value===undefined) return 'na';
  if(value >= target) return 'good';
  const gap = target - value; // hụt bao nhiêu điểm % so với mục tiêu
  if(gap < 0.05) return 'yellow';
  if(gap < 0.15) return 'orange';
  return 'red';
}
function tierColor(tier){ return TIER_COLORS[tier] || TIER_COLORS.na; }
function tierLabel(tier){
  return {good:'Đạt', yellow:'Cần theo dõi', orange:'Cần theo dõi', red:'Chưa đạt', na:'Chưa có dữ liệu'}[tier];
}

// Cột (0-based) trong sheet "Kết quả ND-TN-ATPT"
const COL = {
  THANG:0, NAM:1, LOAI:2, DVGS:3, DVDGS:4,
  ND_SOTH:5, ND_CAUHOI:6, ND_HOTEN:7, ND_NTNS:8, ND_DIACHI:9, ND_MSYT:10, ND_KHONG:11, ND_DATYC:12,
  VT_SONB:13, VT_TRUNGTEN:14, VT_CONVONG:15, VT_MAUSAC:16, VT_THONGTIN:17, VT_TINHTRANG:18, VT_VITRI:19, VT_TYLE:20,
  TN_TONGPHIEU:21, TN_24H:22, TN_THONGTIN:23, TN_TAIDG:24, TN_COBANG:25, TN_DAYDU:26, TN_DUNGMUC:27, TN_TYLE:28,
  ATPT_SOHOSO:29, ATPT_THONGTINNB:30, ATPT_GD1:31, ATPT_GD2:32, ATPT_GD3:33, ATPT_NGUOITH:34, ATPT_BSGM:35, ATPT_PTV:36, ATPT_TYLE:37,
  S5_THANG:38, S5_NAM:39, S5_LOAI:40, S5_DVDG:41, S5_DVDANHGIA:42, S5_SOKHUVUC:43, S5_S1:44, S5_S2:45, S5_S3:46, S5_S4:47, S5_S5:48, S5_TYLE:49
};

const BREAKDOWN_DEF = {
  nhandang: {cols:[COL.ND_CAUHOI, COL.ND_HOTEN, COL.ND_NTNS, COL.ND_DIACHI, COL.ND_MSYT],
             names:["Sử dụng câu hỏi mở","Nhận dạng họ tên người bệnh","Nhận dạng ngày tháng năm sinh","Nhận dạng địa chỉ người bệnh","Đối chiếu mã số y tế"],
             shortNames:["Câu hỏi mở","Họ tên NB","NTNS","Địa chỉ NB","Đối chiếu MSYT"]},
  vongtay: {cols:[COL.VT_MAUSAC, COL.VT_THONGTIN, COL.VT_TINHTRANG, COL.VT_VITRI],
            names:["Màu sắc","Thông tin","Tình trạng vòng","Vị trí đeo"],
            shortNames:["Màu sắc","Thông tin","Tình trạng vòng","Vị trí đeo"]},
  tenga: {cols:[COL.TN_24H, COL.TN_THONGTIN, COL.TN_TAIDG, COL.TN_COBANG, COL.TN_DAYDU, COL.TN_DUNGMUC],
          names:["Đánh giá trong 24h nhập viện","Phiếu đạt thông tin","Tái đánh giá đúng quy định","Có bảng hành động can thiệp","Hành động can thiệp đầy đủ thông tin","Hành động can thiệp đúng mức nguy cơ"],
          shortNames:["Trong 24h nhập viện","Phiếu đạt thông tin","Tái đánh giá đúng QĐ","Có bảng HĐCT","HĐCT đủ thông tin","HĐCT đúng mức nguy cơ"]},
  atpt: {cols:[COL.ATPT_THONGTINNB, COL.ATPT_GD1, COL.ATPT_GD2, COL.ATPT_GD3, COL.ATPT_NGUOITH, COL.ATPT_BSGM, COL.ATPT_PTV],
         names:["Thông tin người bệnh đầy đủ","Giai đoạn 1 đầy đủ","Giai đoạn 2 đầy đủ","Giai đoạn 3 đầy đủ","Thông tin người thực hiện bảng kiểm","Chữ ký bác sĩ gây mê","Chữ ký phẫu thuật viên"],
         shortNames:["Thông tin NB đầy đủ","Giai đoạn 1","Giai đoạn 2","Giai đoạn 3","Người TH bảng kiểm","Chữ ký BSGM","Chữ ký PTV"]},
  "5s": {cols:[COL.S5_S1, COL.S5_S2, COL.S5_S3, COL.S5_S4, COL.S5_S5],
         names:["S1: Sàng lọc","S2: Sắp xếp","S3: Sạch sẽ","S4: Săn sóc","S5: Sẵn sàng"],
         shortNames:["S1: Sàng lọc","S2: Sắp xếp","S3: Sạch sẽ","S4: Săn sóc","S5: Sẵn sàng"]}
};

// ============ TIỆN ÍCH ============
function parseCSV(text){
  const rows = [];
  let row = [], field = '', inQuotes = false;
  for(let i=0;i<text.length;i++){
    const ch = text[i];
    if(inQuotes){
      if(ch === '"'){
        if(text[i+1] === '"'){ field += '"'; i++; } else { inQuotes = false; }
      } else { field += ch; }
    } else {
      if(ch === '"') inQuotes = true;
      else if(ch === ','){ row.push(field); field=''; }
      else if(ch === '\n'){ row.push(field); rows.push(row); row=[]; field=''; }
      else if(ch === '\r'){ /* skip */ }
      else field += ch;
    }
  }
  if(field.length || row.length){ row.push(field); rows.push(row); }
  return rows;
}

function parseNum(raw){
  if(raw===null || raw===undefined) return null;
  let s = String(raw).trim();
  if(s==='') return null;
  const hasPercent = s.includes('%');
  s = s.replace('%','').trim();
  const num = parseFloat(s);
  if(isNaN(num)) return null;
  if(hasPercent) return num/100;
  if(num > 1.5) return num/100; // "85" -> 0.85
  return num; // "0.85" hoặc "1" -> giữ nguyên
}

// Đọc số nguyên thuần (Tháng GS, Năm GS) - KHÔNG áp dụng quy tắc chia 100 như parseNum
function parseIntSafe(raw){
  if(raw===null || raw===undefined) return null;
  const s = String(raw).trim();
  if(s==='') return null;
  const num = parseFloat(s);
  if(isNaN(num)) return null;
  return num;
}

function quarterOf(month){
  if(month===null || month===undefined) return null;
  const m = Math.round(month);
  if(m<1 || m>12) return null;
  return Math.floor((m-1)/3)+1;
}

function avg(list){
  const v = list.filter(x=>x!==null && x!==undefined && !isNaN(x));
  if(!v.length) return null;
  return v.reduce((a,b)=>a+b,0)/v.length;
}

function stripKhoaPrefix(name){
  return (name||'').trim().replace(/^Khoa\s+/i, '').trim();
}

async function fetchCSVRows(url){
  const res = await fetch(url);
  if(!res.ok) throw new Error('HTTP '+res.status);
  const text = await res.text();
  return parseCSV(text);
}

// ============ TẢI DỮ LIỆU THÔ (1 lần) ============
async function loadRaw(urls){
  const [detailRows, aggRows, violRows] = await Promise.all([
    fetchCSVRows(urls.detail),
    fetchCSVRows(urls.aggregate),
    fetchCSVRows(urls.violations)
  ]);

  const depts = [];
  for(let r=2; r<aggRows.length; r++){
    const name = (aggRows[r][0]||'').trim();
    if(name) depts.push(name);
  }

  const byUnitYearMonth = {};
  const availableYears = new Set();

  function ensure(unit, year, month){
    byUnitYearMonth[unit] = byUnitYearMonth[unit] || {};
    byUnitYearMonth[unit][year] = byUnitYearMonth[unit][year] || {};
    byUnitYearMonth[unit][year][month] = byUnitYearMonth[unit][year][month] || {main:[], s5:[]};
    return byUnitYearMonth[unit][year][month];
  }

  for(let r=2; r<detailRows.length; r++){
    const row = detailRows[r];
    if(!row || row.length < 5) continue;

    const loai = (row[COL.LOAI]||'').trim();
    const unit = (row[COL.DVDGS]||'').trim();
    const month = parseIntSafe(row[COL.THANG]);
    const year = parseIntSafe(row[COL.NAM]);
    if(unit && month && year && loai !== 'Tự giám sát'){
      ensure(unit, Math.round(year), Math.round(month)).main.push(row);
      availableYears.add(Math.round(year));
    }

    const loaiS5 = (row[COL.S5_LOAI]||'').trim();
    const unitS5 = stripKhoaPrefix(row[COL.S5_DVDG]);
    const monthS5 = parseIntSafe(row[COL.S5_THANG]);
    const yearS5 = parseIntSafe(row[COL.S5_NAM]);
    if(unitS5 && monthS5 && yearS5 && loaiS5 !== 'Tự giám sát'){
      ensure(unitS5, Math.round(yearS5), Math.round(monthS5)).s5.push(row);
      availableYears.add(Math.round(yearS5));
    }
  }

  const allUnits = new Set([...depts, ...Object.keys(byUnitYearMonth)]);

  const violLookup = {};
  for(let r=1;r<violRows.length;r++){
    const stt = parseInt(violRows[r][14],10);
    const text = violRows[r][15];
    if(!isNaN(stt) && text) violLookup[stt] = text;
  }
  const violDepts = {};
  for(let r=1;r<violRows.length;r++){
    const unit = (violRows[r][0]||'').trim();
    if(!unit) continue;
    const months = [];
    for(let m=1;m<=12;m++) months.push(violRows[r][m]);
    if(!months.some(v=>v!==undefined && v!==null && String(v).trim()!=='')) continue;

    // Gộp (không ghi đè) trong trường hợp 1 đơn vị có nhiều dòng (nhiều đợt giám sát khác nhau)
    if(!violDepts[unit]) violDepts[unit] = new Array(12).fill('');
    for(let m=0;m<12;m++){
      const v = months[m];
      if(v===undefined || v===null || String(v).trim()==='') continue;
      violDepts[unit][m] = violDepts[unit][m] ? (violDepts[unit][m] + ',' + v) : String(v);
    }
  }

  return {
    depts: depts.length ? depts : Array.from(allUnits).sort(),
    allUnits, byUnitYearMonth,
    availableYears: Array.from(availableYears).sort((a,b)=>b-a),
    violations: {lookup: violLookup, depts: violDepts}
  };
}

// ============ TÍNH TOÁN CHO 1 NĂM CỤ THỂ ============
function nhandangScore(rows, unit){
  if(!rows.length) return null;
  if(NHANDANG_MSYT_ONLY.has(unit)){
    return avg(rows.map(r=>parseNum(r[COL.ND_MSYT])));
  }
  const a = avg(rows.map(r=>parseNum(r[COL.ND_DATYC])));
  const b = avg(rows.map(r=>parseNum(r[COL.ND_CAUHOI])));
  const c = avg(rows.map(r=>parseNum(r[COL.ND_MSYT])));
  if(a===null && b===null && c===null) return null;
  return 0.3*(a||0) + 0.4*(b||0) + 0.3*(c||0);
}

function sectionScore(key, rows, unit){
  if(key==='nhandang') return nhandangScore(rows, unit);
  if(key==='vongtay') return avg(rows.map(r=>parseNum(r[COL.VT_TYLE])));
  if(key==='tenga') return avg(rows.map(r=>parseNum(r[COL.TN_TYLE])));
  if(key==='atpt'){
    if(!ATPT_ELIGIBLE.has(unit)) return undefined;
    return avg(rows.map(r=>parseNum(r[COL.ATPT_TYLE])));
  }
  return null;
}

function s5Score(rows){
  return avg(rows.map(r=>parseNum(r[COL.S5_TYLE])));
}

function buildMonthQuarter(months){
  const allUndefined = months.every(v=>v===undefined);
  if(allUndefined) return {months, quarters:[undefined,undefined,undefined,undefined]};
  const quarters = [1,2,3,4].map(q=>{
    const idxs = [ (q-1)*3, (q-1)*3+1, (q-1)*3+2 ];
    const vals = idxs.map(i=>months[i]).filter(v=>v!==null && v!==undefined);
    return vals.length ? avg(vals) : null;
  });
  return {months, quarters};
}

function computeYearData(raw, year){
  const {allUnits, byUnitYearMonth} = raw;
  const sections = {};
  ['nhandang','vongtay','tenga','5s','atpt'].forEach(key=>{ sections[key] = {depts:{}}; });

  allUnits.forEach(unit=>{
    const yearData = (byUnitYearMonth[unit] || {})[year] || {};
    ['nhandang','vongtay','tenga','atpt'].forEach(key=>{
      const months = new Array(12).fill(null);
      const sampleSizes = new Array(12).fill(null);
      for(let m=1;m<=12;m++){
        const rows = (yearData[m]||{main:[]}).main;
        const sc = sectionScore(key, rows, unit);
        months[m-1] = (sc===undefined) ? undefined : sc;
        if(rows.length){
          const s = rows.reduce((sum,r)=> sum + (parseIntSafe(r[SAMPLE_COL[key]])||0), 0);
          sampleSizes[m-1] = s;
        }
      }
      sections[key].depts[unit] = Object.assign(buildMonthQuarter(months), {sampleSizes});
    });
    const months5s = new Array(12).fill(null);
    const sampleSizes5s = new Array(12).fill(null);
    for(let m=1;m<=12;m++){
      const rows = (yearData[m]||{s5:[]}).s5;
      months5s[m-1] = s5Score(rows);
      if(rows.length){
        sampleSizes5s[m-1] = rows.reduce((sum,r)=> sum + (parseIntSafe(r[SAMPLE_COL['5s']])||0), 0);
      }
    }
    sections['5s'].depts[unit] = Object.assign(buildMonthQuarter(months5s), {sampleSizes: sampleSizes5s});
  });

  ['nhandang','vongtay','tenga','atpt','5s'].forEach(key=>{
    const monthsAvg = [];
    for(let m=0;m<12;m++){
      const vals = [];
      allUnits.forEach(u=>{
        const v = sections[key].depts[u].months[m];
        if(v!==null && v!==undefined) vals.push(v);
      });
      monthsAvg.push(avg(vals));
    }
    sections[key].network_avg = buildMonthQuarter(monthsAvg);
  });

  const detailBreakdown = {};
  const rowsByQuarter = {}; // rowsByQuarter[key][unit][quarter] = [raw rows] - phục vụ drill-down
  ['nhandang','vongtay','tenga','atpt','5s'].forEach(key=>{
    detailBreakdown[key] = {names: BREAKDOWN_DEF[key].names, depts:{}};
    rowsByQuarter[key] = {};
  });

  allUnits.forEach(unit=>{
    const yearData = (byUnitYearMonth[unit] || {})[year] || {};
    ['nhandang','vongtay','tenga','atpt'].forEach(key=>{
      const def = BREAKDOWN_DEF[key];
      const byQuarter = {};
      const rowsQ = {};
      for(let m=1;m<=12;m++){
        const q = quarterOf(m);
        const rows = (yearData[m]||{main:[]}).main;
        if(!rows.length) continue;
        byQuarter[q] = byQuarter[q] || def.cols.map(()=>[]);
        rowsQ[q] = (rowsQ[q]||[]).concat(rows.map(r=>({row:r, month:m})));
        def.cols.forEach((c,i)=> rows.forEach(r=>{
          const v = parseNum(r[c]);
          if(v!==null) byQuarter[q][i].push(v);
        }));
      }
      const out = {};
      Object.keys(byQuarter).forEach(q=>{ out[q] = byQuarter[q].map(arr=> arr.length? avg(arr): null); });
      detailBreakdown[key].depts[unit] = out;
      rowsByQuarter[key][unit] = rowsQ;
    });
    const def = BREAKDOWN_DEF['5s'];
    const byQuarter = {};
    const rowsQ = {};
    for(let m=1;m<=12;m++){
      const q = quarterOf(m);
      const rows = (yearData[m]||{s5:[]}).s5;
      if(!rows.length) continue;
      byQuarter[q] = byQuarter[q] || def.cols.map(()=>[]);
      rowsQ[q] = (rowsQ[q]||[]).concat(rows.map(r=>({row:r, month:m})));
      def.cols.forEach((c,i)=> rows.forEach(r=>{
        const v = parseNum(r[c]);
        if(v!==null) byQuarter[q][i].push(v);
      }));
    }
    const out = {};
    Object.keys(byQuarter).forEach(q=>{ out[q] = byQuarter[q].map(arr=> arr.length? avg(arr): null); });
    detailBreakdown['5s'].depts[unit] = out;
    rowsByQuarter['5s'][unit] = rowsQ;
  });

  return {sections, detailBreakdown, rowsByQuarter, year};
}

// ============ RENDER ============
let charts = [];
function destroyCharts(){ charts.forEach(c=>c.destroy()); charts=[]; }
function fmtPct(v){ return (v===null||v===undefined) ? '—' : Math.round(v*100)+'%'; }
function sanitizeSeries(arr){ return arr.map(v => (typeof v === 'number' && isFinite(v)) ? v : null); }

function fmtDelta(delta){
  if(delta===null || delta===undefined) return {text:'—', cls:'delta-flat'};
  const pts = Math.round(delta*100);
  if(pts > 0) return {text:'▲ +'+pts+'%', cls:'delta-up'};
  if(pts < 0) return {text:'▼ '+pts+'%', cls:'delta-down'};
  return {text:'▬ 0%', cls:'delta-flat'};
}

function computeKpiStat(yearData, dept, key, curIdx){
  const target = TARGETS[key];
  if(key==='atpt' && !ATPT_ELIGIBLE.has(dept)) return {na:true};

  const d = yearData.sections[key].depts[dept];
  const prevIdx = curIdx-1;
  const qCur = d ? d.months[curIdx] : null;
  const qPrev = (d && prevIdx>=0) ? d.months[prevIdx] : null;

  // Trung bình 3 tháng gần nhất (tháng hiện tại + 2 tháng trước, bỏ qua tháng thiếu dữ liệu)
  const win = [curIdx, curIdx-1, curIdx-2].filter(i=>i>=0).map(i=> d ? d.months[i] : null);
  const avg3 = avg(win);
  const deltaPrev = (qCur!=null && qPrev!=null) ? (qCur-qPrev) : null;
  const deltaAvg3 = (qCur!=null && avg3!=null) ? (qCur-avg3) : null;

  // Cảnh báo nếu dưới mục tiêu 3 tháng liên tiếp
  const last3 = [curIdx, curIdx-1, curIdx-2];
  const warn = last3.every(i=>i>=0) && last3.every(i=>{
    const v = d ? d.months[i] : null;
    return v!=null && v < target;
  });

  const sampleCur = d && d.sampleSizes ? d.sampleSizes[curIdx] : null;
  const achieved = (qCur!=null && sampleCur) ? Math.round(qCur*sampleCur) : null;

  const tier = tierOf(qCur, target);

  return {na:false, qCur, qPrev, avg3, deltaPrev, deltaAvg3, warn, sampleCur, achieved, tier, target};
}

function renderKPI(yearData, dept, month){
  const grid = document.getElementById('kpiGrid');
  grid.innerHTML = '';
  const curIdx = month-1;
  window.__KPI_STATS__ = {}; // lưu lại để khối "Nhận xét nhanh" dùng chung

  ['nhandang','vongtay','tenga','atpt','5s'].forEach(key=>{
    const color = SECTION_COLORS[key];
    const card = document.createElement('div');
    card.className = 'kpi-card';
    card.style.setProperty('--kpi-color', color);

    const stat = computeKpiStat(yearData, dept, key, curIdx);
    window.__KPI_STATS__[key] = stat;

    if(stat.na){
      card.innerHTML = `
        <div class="kpi-line title-line">
          <div class="kpi-line-left"><div class="kpi-title">${SECTION_TITLES[key]}</div></div>
          <div class="kpi-value na">—</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-line"><span class="kpi-na">Không áp dụng cho đơn vị này</span></div>
      `;
      grid.appendChild(card);
      return;
    }

    const {qCur, qPrev, deltaPrev, warn, sampleCur, tier, target} = stat;
    const dPrev = fmtDelta(deltaPrev);
    const tColor = tierColor(tier);
    const prevMonthTag = curIdx-1>=0 ? 'T'+(curIdx) : '—';
    const isGood = tier==='good';
    const badgeLabel = isGood ? 'Đạt' : 'Không đạt';
    const badgeCls = isGood ? 'badge-good' : 'badge-bad';

    card.innerHTML = `
      <div class="kpi-line title-line">
        <div class="kpi-line-left">
          <div class="kpi-title">
            ${SECTION_TITLES[key]}
            ${warn?'<span class="warn-icon" title="Dưới mục tiêu 3 tháng liên tiếp">⚠</span>':''}
          </div>
        </div>
        <div class="kpi-value" style="color:${tColor}">${fmtPct(qCur)}</div>
      </div>
      <div class="kpi-divider"></div>
      <div class="kpi-line">
        <span class="kpi-target">Mục tiêu ≥${Math.round(target*100)}%</span>
        <span class="kpi-badge ${badgeCls}">${badgeLabel}</span>
      </div>
      <div class="kpi-line">
        <span class="kpi-sample">${sampleCur ? sampleCur+' '+SAMPLE_UNIT_LABEL[key] : '—'}</span>
        <span class="delta-chip ${dPrev.cls}">${prevMonthTag}: ${fmtPct(qPrev)} ${dPrev.text}</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderQuickNote(container, yearData, dept, month){
  const stats = window.__KPI_STATS__ || {};
  const applicableKeys = Object.keys(stats).filter(k=>!stats[k].na && stats[k].tier!=='na');

  if(!applicableKeys.length){
    container.innerHTML = `<h3>💡 Nhận xét nhanh</h3><p class="qn-empty">Chưa đủ dữ liệu giám sát trong tháng này để đưa ra nhận định.</p>`;
    return;
  }

  const curVals = applicableKeys.map(k=>stats[k].qCur).filter(v=>v!=null);
  const prevVals = applicableKeys.map(k=>stats[k].qPrev).filter(v=>v!=null);
  const avgCur = avg(curVals);
  const avgPrev = avg(prevVals);
  const avgDelta = (avgCur!=null && avgPrev!=null) ? avgCur-avgPrev : null;
  let avgDeltaTxt = '';
  if(avgDelta!=null){
    const pts = Math.round(Math.abs(avgDelta)*100);
    avgDeltaTxt = avgDelta<0 ? `, giảm ${pts}% so với tháng trước` : (avgDelta>0 ? `, tăng ${pts}% so với tháng trước` : ', không đổi so với tháng trước');
  }

  const cleanTitle = k => SECTION_TITLES[k].replace(/\u00A0/g,' ');
  const goodKeys = applicableKeys.filter(k=>stats[k].tier==='good');
  const badKeys = applicableKeys.filter(k=>stats[k].tier!=='good').sort((a,b)=>{
    const order = {red:0, orange:1, yellow:2};
    return order[stats[a].tier]-order[stats[b].tier];
  });

  let bulletsHtml = '';
  if(goodKeys.length){
    bulletsHtml += `<li><span class="qn-icon-ok">✅</span> Nhóm ${goodKeys.map(k=>'"'+cleanTitle(k)+'"').join(', ')} duy trì kết quả tốt, đạt mục tiêu.</li>`;
  }
  if(badKeys.length){
    const worstKey = badKeys[0];
    const warn3 = stats[worstKey].warn;
    bulletsHtml += `<li><span class="qn-icon-warn">⚠️</span> Nhóm "${cleanTitle(worstKey)}" ${warn3?'dưới mục tiêu 3 tháng liên tiếp, ':''}cần ưu tiên xử lý.</li>`;
  }

  // Vấn đề ưu tiên: top tiêu chí con thấp nhất dưới mục tiêu trong quý chứa tháng đang chọn
  const quarter = quarterOf(month);
  const items = [];
  ['nhandang','vongtay','tenga','atpt','5s'].forEach(key=>{
    if(key==='atpt' && !ATPT_ELIGIBLE.has(dept)) return;
    const def = BREAKDOWN_DEF[key];
    const dd = yearData.detailBreakdown[key].depts[dept];
    if(!dd) return;
    const values = dd[quarter];
    if(!values) return;
    values.forEach((v,i)=>{
      if(v===null || v===undefined) return;
      const target = TARGETS[key];
      if(v>=target) return;
      items.push({name:def.names[i], value:v, target, gap:target-v, tier:tierOf(v,target)});
    });
  });
  items.sort((a,b)=> b.gap-a.gap);
  const top2 = items.slice(0,2);
  const priorityHtml = top2.length ? top2.map(it=>{
    const icon = it.tier==='red' ? '🔴' : (it.tier==='orange' ? '🟠' : '🟡');
    return `<div class="qn-priority-item">${icon} <span><b>${it.name}</b> — ${Math.round(it.value*100)}%, thiếu ${Math.round(it.gap*100)}% so với mục tiêu</span></div>`;
  }).join('') : '<div class="qn-priority-item">✅ Tất cả tiêu chí con đều đạt mục tiêu trong quý.</div>';

  // Khuyến nghị hành động
  let recoText = 'Duy trì kết quả hiện tại và tiếp tục giám sát định kỳ theo kế hoạch.';
  if(badKeys.length){
    const worstKey = badKeys[0];
    const worstCritName = top2.length ? top2[0].name : cleanTitle(worstKey);
    recoText = `Đề nghị khoa rà soát quy trình liên quan đến "${worstCritName}" và tăng cường giám sát chéo trong tháng tới đối với nội dung ${cleanTitle(worstKey).toLowerCase()}.`;
  }

  container.innerHTML = `
    <h3>💡 Nhận xét nhanh</h3>
    <p class="qn-summary">Tỷ lệ chung tháng ${month}/${yearData.year} đạt <b>${avgCur!=null?Math.round(avgCur*100)+'%':'—'}</b>${avgDeltaTxt}.</p>
    <ul class="qn-bullets">${bulletsHtml}</ul>
    <div>
      <div class="qn-subhead">Vấn đề ưu tiên</div>
      ${priorityHtml}
    </div>
    <div>
      <div class="qn-subhead">Khuyến nghị hành động</div>
      <p class="qn-reco">${recoText}</p>
    </div>
  `;
}

function closeDrillDown(){ document.getElementById('drillModal').classList.remove('open'); }

function openDrillDown(sectionKey, dept, quarter, critIdx, yearData, critName, targetVal){
  const modal = document.getElementById('drillModal');
  document.getElementById('drillModalTitle').textContent = `${SECTION_TITLES[sectionKey]} — ${critName}`;
  const body = document.getElementById('drillModalBody');
  const rq = yearData.rowsByQuarter[sectionKey][dept];
  const rowsInfo = rq ? rq[quarter] : null;

  if(!rowsInfo || !rowsInfo.length){
    body.innerHTML = '<div class="viol-empty">Không có phiên giám sát nào trong quý này.</div>';
  } else {
    const def = BREAKDOWN_DEF[sectionKey];
    const colIdx = def.cols[critIdx];
    const rowsHtml = rowsInfo.map(({row,month})=>{
      const loai = sectionKey==='5s' ? row[COL.S5_LOAI] : row[COL.LOAI];
      const donvi = sectionKey==='5s' ? row[COL.S5_DVDANHGIA] : row[COL.DVGS];
      const v = parseNum(row[colIdx]);
      const vTxt = v===null ? '—' : Math.round(v*100)+'%';
      const below = v!==null && v<targetVal;
      return `<tr><td>Tháng ${month}</td><td>${loai||'—'}</td><td>${donvi||'—'}</td><td style="color:${below?ALERT:INK};font-weight:${below?700:400}">${vTxt}</td></tr>`;
    }).join('');
    body.innerHTML = `
      <p class="drill-note">Dữ liệu ở mức phiên giám sát — không có thông tin định danh từng người bệnh cụ thể trong nguồn dữ liệu hiện tại.</p>
      <table class="viol-table">
        <thead><tr><th>Kỳ giám sát</th><th>Loại giám sát</th><th>Đơn vị thực hiện</th><th>Tỷ lệ tiêu chí này</th></tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    `;
  }
  modal.classList.add('open');
}

function overviewTrendChart(body, yearData, dept){
  body.innerHTML = '<div class="trend-canvas-wrap"><canvas></canvas></div><div class="legend"></div>';
  const ctx = body.querySelector('canvas').getContext('2d');
  const legend = body.querySelector('.legend');
  legend.innerHTML = ['nhandang','vongtay','tenga','atpt','5s'].map(key=>
    `<span class="legend-item"><span class="sw" style="background:${SECTION_COLORS[key]}"></span>${SECTION_TITLES[key]}</span>`
  ).join('');

  const datasets = ['nhandang','vongtay','tenga','atpt','5s'].map(key=>{
    const d = yearData.sections[key].depts[dept];
    const raw = d ? d.months.map(v=> (v===null||v===undefined)? null : v*100) : new Array(12).fill(null);
    return {label:SECTION_TITLES[key], data:sanitizeSeries(raw), borderColor:SECTION_COLORS[key], backgroundColor:SECTION_COLORS[key],
             borderWidth:2.5, tension:0.3, spanGaps:true, pointRadius:3, pointBackgroundColor:SECTION_COLORS[key]};
  });

  const chart = new Chart(ctx, {
    type:'line',
    data:{labels:MONTH_LABELS, datasets},
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false}, tooltip:{callbacks:{label:(item)=>`${item.dataset.label}: ${item.raw===null?'—':Math.round(item.raw)+'%'}`}}},
      scales:{
        y:{min:0,max:100,ticks:{callback:v=>v+'%',font:{family:"'Inter', sans-serif",size:12}},grid:{color:'#EEF4F9'}},
        x:{grid:{display:false},ticks:{font:{family:"'Inter', sans-serif",size:12}}}
      }
    }
  });
  charts.push(chart);
}

function wrapLabelForNarrow(label){
  // Xuống dòng tại khoảng trắng gần giữa nhất (không cắt giữa chữ)
  if(label.length <= 12) return label;
  const mid = Math.floor(label.length/2);
  let bestIdx = -1, bestDist = Infinity;
  for(let i=0;i<label.length;i++){
    if(label[i]===' '){
      const dist = Math.abs(i-mid);
      if(dist<bestDist){ bestDist=dist; bestIdx=i; }
    }
  }
  if(bestIdx===-1) return label;
  return [label.slice(0,bestIdx), label.slice(bestIdx+1)];
}

function breakdownBarChart(body, names, values, targetVal, sectionKey, dept, quarter, yearData, fullNames){
  body.innerHTML = '<div class="breakdown-canvas-wrap"><canvas></canvas></div>';
  const canvas = body.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const data = values.map(v => v===null||v===undefined ? null : v*100);
  const barColors = data.map(v => v===null ? TIER_COLORS.na : tierColor(tierOf(v/100, targetVal)));

  const valueLabelPlugin = {
    id:'vl_'+Math.random().toString(36).slice(2),
    afterDatasetsDraw(chart){
      const meta = chart.getDatasetMeta(0);
      const c = chart.ctx; c.save();
      c.font = "600 12px 'Inter', sans-serif";
      c.textAlign='left'; c.textBaseline='middle';
      meta.data.forEach((bar,i)=>{
        const val = data[i];
        if(val===null||val===undefined) return;
        c.fillStyle = barColors[i];
        c.fillText(Math.round(val)+'%', bar.x+6, bar.y);
      });
      c.restore();
    }
  };
  const targetLabelPlugin = {
    id:'tl_'+Math.random().toString(36).slice(2),
    afterDatasetsDraw(chart){
      const xScale = chart.scales.x, area = chart.chartArea;
      const xPix = xScale.getPixelForValue(targetVal*100);
      const c = chart.ctx; c.save();
      c.font = "600 12px 'Inter', sans-serif";
      c.fillStyle = TARGET_LINE; c.textBaseline='bottom';
      const label = 'Mục tiêu '+Math.round(targetVal*100)+'%';
      const textW = c.measureText(label).width;
      let tx = xPix; c.textAlign='center';
      if(xPix-textW/2 < area.left){ c.textAlign='left'; tx=area.left; }
      if(xPix+textW/2 > area.right){ c.textAlign='right'; tx=area.right; }
      c.fillText(label, tx, area.top-4);
      c.restore();
    }
  };

  canvas.style.cursor = 'pointer';
  const isNarrow = window.innerWidth <= 480;
  const yLabels = isNarrow ? names.map(wrapLabelForNarrow) : names;
  const chart = new Chart(ctx, {
    type:'bar',
    data:{labels:yLabels, datasets:[
      {label:'Tỷ lệ đạt', data, backgroundColor:barColors, borderRadius:4},
      {label:'Mục tiêu', data:new Array(names.length).fill(targetVal*100), type:'line', borderColor:TARGET_LINE, borderWidth:1.5, borderDash:[2,3], pointRadius:0, tension:0}
    ]},
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      layout:{padding:{right:55, top:22}},
      plugins:{legend:{display:false}},
      onClick:(evt, elements)=>{
        if(!elements.length) return;
        const idx = elements[0].index;
        openDrillDown(sectionKey, dept, quarter, idx, yearData, (fullNames||names)[idx], targetVal);
      },
      scales:{
        x:{min:0,max:100,ticks:{stepSize:20,callback:v=>Math.round(v)+'%',font:{family:"'Inter', sans-serif",size:12}},grid:{color:'#EEF4F9'}},
        y:{
          grid:{display:false},
          ticks:{font:{family:"'Inter', sans-serif",size:isNarrow?11:12}},
          afterFit(scale){ scale.width = isNarrow ? 78 : 168; }
        }
      }
    },
    plugins:[valueLabelPlugin, targetLabelPlugin]
  });
  charts.push(chart);
}

function wrapMultiLine(text, maxLineLen, maxChars){
  let t = String(text).trim();
  if(maxChars && t.length > maxChars) t = t.slice(0, maxChars-1).trim() + '…';
  const words = t.split(/\s+/);
  const lines = [];
  let cur = '';
  words.forEach(w=>{
    if(cur && (cur+' '+w).length > maxLineLen){ lines.push(cur); cur = w; }
    else cur = cur ? cur+' '+w : w;
  });
  if(cur) lines.push(cur);
  return lines;
}

function renderParetoCard(body, raw, dept, month){
  const monthsArr = raw.violations.depts[dept];
  if(!monthsArr){
    body.innerHTML = '<div class="chart-empty">Không có dữ liệu lỗi vi phạm cho đơn vị này.</div>';
    return;
  }
  const counts = {};
  for(let idx=0; idx<12; idx++){
    const cell = monthsArr[idx];
    if(cell===undefined || cell===null || String(cell).trim()==='') continue;
    String(cell).replace(/[^0-9]/g,'').split('').forEach(d=>{ counts[d]=(counts[d]||0)+1; });
  }
  const codes = Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
  if(!codes.length){
    body.innerHTML = '<div class="chart-empty">Không ghi nhận lỗi vi phạm nào trong năm đang chọn.</div>';
    return;
  }
  const total = codes.reduce((s,c)=>s+counts[c],0);
  let cum = 0;
  const cumPct = codes.map(c=>{ cum += counts[c]; return Math.round(cum/total*100); });
  const fullTexts = codes.map(c=> raw.violations.lookup[parseInt(c,10)] || ('Mã '+c));
  const labels = fullTexts.map(t=> wrapMultiLine(t, 13, 45));

  body.innerHTML = '<div class="pareto-wrap"><canvas></canvas></div>';
  const canvas = body.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const chart = new Chart(ctx, {
    type:'bar',
    data:{
      labels,
      datasets:[
        {type:'bar', label:'Số lần', data: codes.map(c=>counts[c]), backgroundColor:'#B8402A', borderRadius:4, yAxisID:'yCount', order:2},
        {type:'line', label:'% tích lũy', data: cumPct, borderColor:'#004C85', backgroundColor:'#004C85', borderWidth:2, borderDash:[4,3], pointRadius:3, tension:0.25, yAxisID:'yPct', order:1}
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:true, position:'bottom', labels:{font:{family:"'Inter', sans-serif", size:11}, boxWidth:12}},
        tooltip:{callbacks:{
          title:(items)=> 'Mã lỗi '+codes[items[0].dataIndex],
          afterLabel:(c)=> c.datasetIndex===0 ? fullTexts[c.dataIndex] : ''
        }}
      },
      scales:{
        yCount:{position:'left', beginAtZero:true, ticks:{font:{family:"'Inter', sans-serif", size:11}}},
        yPct:{position:'right', min:0, max:100, grid:{drawOnChartArea:false}, ticks:{callback:v=>v+'%', font:{family:"'Inter', sans-serif", size:11}}},
        x:{ticks:{font:{family:"'Inter', sans-serif", size:10.5}, maxRotation:0, minRotation:0}}
      }
    }
  });
  charts.push(chart);
}

function renderCharts(yearData, dept, month, raw){
  const trendRow = document.getElementById('trendRow');
  const grid = document.getElementById('chartGrid');
  trendRow.innerHTML = '';
  grid.innerHTML = '';
  destroyCharts();
  const quarter = quarterOf(month);

  const wideCard = document.createElement('div');
  wideCard.className = 'card wide';
  wideCard.innerHTML = `<h3>Xu hướng</h3><div class="body"></div>`;
  trendRow.appendChild(wideCard);
  try{
    overviewTrendChart(wideCard.querySelector('.body'), yearData, dept);
  } catch(err){
    wideCard.querySelector('.body').innerHTML = `<div class="chart-empty">Không vẽ được biểu đồ (${err.message}).</div>`;
  }

  const quickNoteCard = document.createElement('div');
  quickNoteCard.className = 'quicknote-card';
  trendRow.appendChild(quickNoteCard);
  try{
    renderQuickNote(quickNoteCard, yearData, dept, month);
  } catch(err){
    quickNoteCard.innerHTML = `<h3>💡 Nhận xét nhanh</h3><p class="qn-empty">Không tạo được nhận xét (${err.message}).</p>`;
  }

  ['nhandang','vongtay','tenga','atpt','5s'].forEach(key=>{
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `<h3>${SECTION_TITLES[key]}</h3><div class="body"></div>`;
    grid.appendChild(card);
    const body = card.querySelector('.body');

    if(key==='atpt' && !ATPT_ELIGIBLE.has(dept)){
      body.innerHTML = '<div class="chart-empty">Nội dung ATPT không áp dụng cho đơn vị này.</div>';
      return;
    }

    try{
      const dd = yearData.detailBreakdown[key].depts[dept];
      const values = dd ? dd[quarter] : null;
      if(values && values.some(v=>v!==null)){
        const def = BREAKDOWN_DEF[key];
        breakdownBarChart(body, def.shortNames, values, TARGETS[key], key, dept, quarter, yearData, def.names);
      } else {
        body.innerHTML = '<div class="chart-empty">Chưa có dữ liệu bóc tách tiêu chí cho đơn vị này trong quý chứa tháng đang chọn.</div>';
      }
    } catch(err){
      body.innerHTML = `<div class="chart-empty">Không vẽ được biểu đồ (${err.message}).</div>`;
    }
  });

  const paretoCard = document.createElement('div');
  paretoCard.className = 'card';
  paretoCard.innerHTML = `<h3>Lỗi vi phạm qua các tháng</h3><div class="body"></div>`;
  grid.appendChild(paretoCard);
  try{
    renderParetoCard(paretoCard.querySelector('.body'), raw, dept, month);
  } catch(err){
    paretoCard.querySelector('.body').innerHTML = `<div class="chart-empty">Không vẽ được biểu đồ (${err.message}).</div>`;
  }
}

function renderViol(raw, dept, month){
  const card = document.getElementById('violCard');
  const monthsArr = raw.violations.depts[dept];
  const labels = ['Tháng 1','Tháng 2','Tháng 3','Tháng 4','Tháng 5','Tháng 6','Tháng 7','Tháng 8','Tháng 9','Tháng 10','Tháng 11','Tháng 12'];
  const cell = monthsArr ? monthsArr[month-1] : null;
  const hasCurrentMonth = monthsArr && cell && String(cell).trim()!=='';

  // Gộp toàn bộ ghi chú cả năm (dùng cho bảng chi tiết + kiểm tra có dữ liệu để hiện nút hay không)
  let fullRows = '';
  let hasAnyYear = false;
  if(monthsArr){
    monthsArr.forEach((c,i)=>{
      if(c===undefined || c===null || String(c).trim()==='') return;
      String(c).replace(/[^0-9]/g,'').split('').forEach(d=>{
        const text = raw.violations.lookup[parseInt(d,10)] || ('Ghi chú: '+c);
        fullRows += `<tr><td><span class="month-chip">${labels[i]}</span></td><td>${text}</td></tr>`;
        hasAnyYear = true;
      });
    });
  }

  let bodyHtml;
  if(!hasCurrentMonth){
    bodyHtml = `<div class="viol-empty">Tháng ${month}: không ghi nhận lưu ý nào trong quá trình giám sát đối với đơn vị này.</div>`;
  } else {
    const digits = String(cell).replace(/[^0-9]/g,'').split('');
    const counts = {};
    digits.forEach(d=>{ counts[d] = (counts[d]||0)+1; });
    const total = digits.length;
    const top3 = Object.keys(counts).sort((a,b)=>counts[b]-counts[a]).slice(0,3);
    const top3Html = top3.map(code=>{
      const text = raw.violations.lookup[parseInt(code,10)] || ('Ghi chú: '+cell);
      return `<li>${counts[code]} lượt — ${text}</li>`;
    }).join('');
    bodyHtml = `
      <div class="viol-month">Tháng ${month}</div>
      <div class="viol-count">Có ${total} ghi chú</div>
      <ul class="viol-top3">${top3Html}</ul>
    `;
  }

  const toggleBtnHtml = hasAnyYear ? `<button id="violToggle" class="viol-toggle-btn">Xem chi tiết cả năm</button>` : '';

  card.innerHTML = `
    ${bodyHtml}
    ${toggleBtnHtml}
    <div id="violDetail" class="viol-detail" style="display:none">
      <table class="viol-table"><thead><tr><th style="width:110px">Tháng</th><th>Lưu ý ghi nhận trong giám sát</th></tr></thead><tbody>${fullRows}</tbody></table>
    </div>
  `;
  if(hasAnyYear){
    const btn = document.getElementById('violToggle');
    btn.onclick = ()=>{
      const det = document.getElementById('violDetail');
      const show = det.style.display==='none';
      det.style.display = show?'block':'none';
      btn.textContent = show?'Ẩn chi tiết':'Xem chi tiết cả năm';
    };
  }
}

// ============ TRẠNG THÁI & KHỞI ĐỘNG ============
let RAW = null;
let YEAR_DATA = null;
let STATE = {dept:null, year:null, month:null};

function renderAll(){
  if(!RAW || !YEAR_DATA || !STATE.dept) return;
  document.getElementById('unitNameOut').textContent = STATE.dept;
  renderKPI(YEAR_DATA, STATE.dept, STATE.month);          // cũng set window.__KPI_STATS__
  renderCharts(YEAR_DATA, STATE.dept, STATE.month, RAW);
  renderViol(RAW, STATE.dept, STATE.month);
}

function populateYearSelect(raw, curYear){
  const yearSelect = document.getElementById('yearSelect');
  const years = new Set(raw.availableYears);
  years.add(curYear);
  const sorted = Array.from(years).sort((a,b)=>b-a);
  yearSelect.innerHTML = '';
  sorted.forEach(y=>{
    const opt = document.createElement('option');
    opt.value = y; opt.textContent = 'Năm '+y;
    yearSelect.appendChild(opt);
  });
}

function populateMonthSelect(){
  const monthSelect = document.getElementById('monthSelect');
  monthSelect.innerHTML = '';
  for(let m=1;m<=12;m++){
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = 'Tháng '+m;
    monthSelect.appendChild(opt);
  }
}

async function boot(urls){
  const statusEl = document.getElementById('statusMsg');
  const deptSelect = document.getElementById('deptSelect');
  statusEl.textContent = 'Đang tải dữ liệu từ Google Sheet...';
  statusEl.className = 'status loading';
  try{
    RAW = await loadRaw(urls);
    statusEl.textContent = '';
    statusEl.className = 'status';

    deptSelect.innerHTML = '';
    RAW.depts.forEach(d=>{
      const opt = document.createElement('option');
      opt.value = d; opt.textContent = d;
      deptSelect.appendChild(opt);
    });

    const now = new Date();
    const curYear = now.getFullYear();
    const curMonth = now.getMonth()+1;

    populateYearSelect(RAW, curYear);
    populateMonthSelect();

    document.getElementById('yearSelect').value = curYear;
    document.getElementById('monthSelect').value = curMonth;
    deptSelect.value = RAW.depts[0];

    STATE = {dept: RAW.depts[0], year: curYear, month: curMonth};
    YEAR_DATA = computeYearData(RAW, STATE.year);
    renderAll();

    deptSelect.onchange = ()=>{ STATE.dept = deptSelect.value; renderAll(); };
    document.getElementById('monthSelect').onchange = (e)=>{ STATE.month = parseInt(e.target.value,10); renderAll(); };
    document.getElementById('yearSelect').onchange = (e)=>{
      STATE.year = parseInt(e.target.value,10);
      YEAR_DATA = computeYearData(RAW, STATE.year);
      renderAll();
    };
  } catch(err){
    statusEl.textContent = 'Không tải được dữ liệu (' + err.message + '). Kiểm tra: Sheet có ở chế độ "Bất kỳ ai có đường liên kết đều xem được" chưa, và trình duyệt có kết nối mạng không.';
    statusEl.className = 'status error';
  }
}

document.getElementById('refreshBtn').addEventListener('click', ()=> boot(window.__CSV_URLS__));
document.getElementById('printBtn').addEventListener('click', ()=> window.print());
document.getElementById('drillModalClose').addEventListener('click', closeDrillDown);
document.getElementById('drillModal').addEventListener('click', (e)=>{ if(e.target.id==='drillModal') closeDrillDown(); });
"""

CSS = """
:root{
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
  --bg:#F6F8FA; --surface:#FFFFFF; --ink:#1B2733; --muted:#5C6B7A; --faint:#94A3B3; --line:#E1E7ED;

  /* Thang cỡ chữ */
  --fs-dashboard-title: 30px;
  --fs-section-title: 22px;
  --fs-card-title: 17px;
  --fs-card-value: 42px;
  --fs-normal: 16px;
  --fs-small: 14px;
  --fs-caption: 13px;
}
*{box-sizing:border-box;}
body{
  margin:0;background:var(--bg);color:var(--ink);font-family:var(--font);
  font-weight:400;font-size:var(--fs-normal);line-height:1.5;letter-spacing:0;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1280px;margin:0 auto;padding:20px 24px 48px;}

/* --- Header: gọn, 1 hàng trên desktop --- */
.header-bar{
  display:flex;align-items:center;flex-wrap:nowrap;gap:14px 20px;
  padding-bottom:14px;margin-bottom:20px;border-bottom:2px solid var(--ink);
}
.header-title-block{margin-right:auto;flex:1 1 auto;min-width:0;}
.brand-eyebrow{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#004C85;margin:0;line-height:1.4;}
.brand-title{font-size:24px;font-weight:700;letter-spacing:-0.02em;line-height:1.25;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.brand-title .title-short{display:none;}
@media(max-width:480px){
  .brand-title .title-full{display:none;}
  .brand-title .title-short{display:inline;}
}
.header-controls{display:flex;align-items:center;flex-wrap:wrap;gap:8px 10px;flex:0 0 auto;}
.header-controls .select-wrap select{padding:9px 30px 9px 12px;font-size:13px;}
#deptSelect{width:220px;max-width:100%;}
#monthSelect, #yearSelect{width:104px;}
.header-btn-group{display:flex;gap:8px;}

/* Tablet: thu nhỏ select + tiêu đề để header không tràn dòng, nút luôn ở bên phải (header-bar giữ nowrap) */
@media(max-width:1024px) and (min-width:769px){
  .brand-title{font-size:20px;}
  #deptSelect{width:150px;}
  #monthSelect, #yearSelect{width:84px;}
  .header-controls .select-wrap select{padding:8px 26px 8px 10px;font-size:12.5px;}
}

.btn-secondary, #refreshBtn{
  font-family:var(--font);font-size:var(--fs-small);font-weight:500;color:#004C85;background:#fff;
  border:1px solid var(--line);border-radius:6px;padding:9px 14px;cursor:pointer;letter-spacing:0;
  white-space:nowrap;transition:background 150ms ease;
}
.btn-secondary:hover, #refreshBtn:hover{background:#F0F5FA;}

.status{font-size:var(--fs-caption);padding:0 0 10px;min-height:0;}
.status.loading{color:var(--muted);}
.status.error{color:#B8402A;font-weight:500;}

.selector-block{display:flex;flex-direction:column;gap:4px;}
.selector-label{display:none;} /* nhãn ẩn để gọn header 1 hàng, select đã đủ rõ nghĩa */
.select-wrap select{
  appearance:none;-webkit-appearance:none;
  background:var(--surface) url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="%23004C85" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>') no-repeat right 12px center;
  border:1.5px solid #B9CBDA;border-radius:6px;font-weight:500;color:#1B2733;
  font-family:var(--font);cursor:pointer;letter-spacing:0;transition:border-color 150ms ease, box-shadow 150ms ease;
}
.select-wrap select:focus{outline:none;border-color:#004C85;box-shadow:0 0 0 3px rgba(0,76,133,0.15);}

.section-title{
  font-size:var(--fs-section-title);font-weight:600;letter-spacing:-0.01em;line-height:1.3;
  margin:32px 0 16px;display:flex;align-items:baseline;gap:10px;
}
.section-title .num{font-size:11px;font-weight:700;color:#004C85;letter-spacing:.06em;}

/* --- Khối KPI (compact) --- */
.kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:8px;}
@media(max-width:1024px){.kpi-grid{grid-template-columns:repeat(3,1fr);}}
@media(max-width:640px){.kpi-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:360px){.kpi-grid{grid-template-columns:1fr;}}

.kpi-card{
  background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--kpi-color,#004C85);border-radius:10px;
  padding:12px 14px;display:flex;flex-direction:column;gap:6px;
  transition:box-shadow 200ms ease, transform 200ms ease;
}
.kpi-card:hover{box-shadow:0 4px 14px rgba(27,39,51,0.08);transform:scale(1.01);}
.kpi-line{display:flex;align-items:center;justify-content:space-between;gap:10px;}
.kpi-line.title-line{align-items:flex-start;}
.kpi-line-left{min-width:0;flex:1;}
.kpi-title{display:flex;align-items:center;gap:5px;font-weight:600;font-size:13px;line-height:1.3;
  min-width:0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.kpi-na{font-size:12px;color:var(--faint);line-height:1.4;}
.kpi-value{font-size:22px;font-weight:600;line-height:1;flex:none;}
.kpi-value.na{font-size:13px;color:var(--faint);font-weight:500;}
.kpi-target, .kpi-sample{font-size:11px;color:var(--faint);}
.kpi-badge{font-size:10.5px;font-weight:600;padding:2px 8px;border-radius:6px;white-space:nowrap;flex:none;}
.delta-chip{font-weight:600;padding:2px 7px;border-radius:20px;font-size:10.5px;white-space:nowrap;flex:none;}
.delta-up{background:#E7F4EC;color:#1E8A57;}
.delta-down{background:#FBEAE5;color:#B8402A;}
.delta-flat{background:#F1F4F7;color:var(--muted);}
.warn-icon{color:#B8402A;font-size:12px;flex:none;}
.kpi-divider{border-top:1px dashed var(--line);margin:1px 0;}
.badge-good{background:#E7F4EC;color:#1E8A57;}
.badge-bad{background:#FBEAE5;color:#B8402A;}

/* --- Biểu đồ --- */
.trend-notes-grid{display:grid;grid-template-columns:2fr 1fr;gap:14px;align-items:stretch;margin-bottom:14px;}
@media(max-width:900px){.trend-notes-grid{grid-template-columns:1fr;}}
.trend-notes-grid .card.wide{grid-column:auto;}
.chart-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;}
@media(max-width:768px){.chart-grid{grid-template-columns:1fr;}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px;transition:box-shadow 200ms ease, transform 200ms ease;}
.card:hover{box-shadow:0 4px 14px rgba(27,39,51,0.07);transform:scale(1.01);}
.card.wide{grid-column:1/-1;}
.card h3{font-size:var(--fs-card-title);font-weight:600;margin:0 0 10px;letter-spacing:-0.01em;}
.trend-canvas-wrap{position:relative;height:360px;}
@media(max-width:1024px){.trend-canvas-wrap{height:300px;}}
@media(max-width:640px){.trend-canvas-wrap{height:230px;}}
@media(max-width:480px){.trend-canvas-wrap{height:170px;}}
.breakdown-canvas-wrap{position:relative;height:190px;}
@media(max-width:480px){.breakdown-canvas-wrap{height:240px;}}
.pareto-wrap{position:relative;height:235px;}
@media(max-width:480px){.pareto-wrap{height:275px;}}
.card:not(.wide) .body, .card:not(.wide) .chart-empty{min-height:190px;display:flex;flex-direction:column;justify-content:center;}
@media(max-width:480px){.card:not(.wide) .body, .card:not(.wide) .chart-empty{min-height:240px;}}
.legend{display:flex;gap:14px;font-size:var(--fs-caption);color:var(--muted);margin-top:10px;flex-wrap:wrap;justify-content:center;}
@media(min-width:769px) and (max-width:1023px){.legend{display:grid;grid-template-columns:repeat(3,auto);justify-content:center;gap:8px 18px;}}
.legend-item{display:flex;align-items:center;gap:6px;}
.sw{width:13px;height:9px;border-radius:2px;display:inline-block;flex:none;}
.chart-empty{font-size:var(--fs-small);color:var(--faint);padding:20px 12px;text-align:center;}

/* --- Nhận xét nhanh (gộp nhận định + ưu tiên cải tiến + khuyến nghị) --- */
.quicknote-card{background:#FFFDF7;border:1px solid #F0DEA8;border-radius:10px;padding:16px;display:flex;flex-direction:column;gap:12px;}
.quicknote-card h3{font-size:var(--fs-card-title);font-weight:600;margin:0;letter-spacing:-0.01em;}
.qn-empty{font-size:var(--fs-small);color:var(--muted);margin:0;}
.qn-summary{font-size:var(--fs-small);line-height:1.6;color:var(--ink);margin:0;}
.qn-bullets{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;}
.qn-bullets li{font-size:var(--fs-caption);line-height:1.5;display:flex;gap:7px;}
.qn-icon-ok{color:#1E8A57;flex:none;}
.qn-icon-warn{color:#D9822B;flex:none;}
.qn-subhead{font-size:var(--fs-caption);font-weight:700;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);margin:0 0 6px;border-top:1px dashed #E9DBAF;padding-top:12px;}
.qn-priority-item{font-size:var(--fs-caption);line-height:1.5;margin-bottom:6px;display:flex;gap:6px;}
.qn-priority-item b{font-weight:600;}
.qn-reco{font-size:var(--fs-caption);line-height:1.6;color:var(--ink);margin:0;}

/* --- Ghi chú giám sát --- */
.viol-card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 18px;}
.viol-empty{color:var(--faint);font-size:var(--fs-small);padding:4px 0;}
.viol-month{font-size:17px;font-weight:600;color:var(--ink);}
.viol-count{font-size:var(--fs-small);color:var(--ink);margin:2px 0 10px;}
.viol-top3{margin:0 0 12px;padding-left:20px;font-size:var(--fs-small);line-height:1.6;color:var(--ink);}
.viol-toggle-btn{
  font-family:var(--font);font-size:var(--fs-caption);font-weight:600;color:#004C85;background:#F0F5FA;
  border:1px solid var(--line);border-radius:6px;padding:6px 12px;cursor:pointer;
}
.viol-toggle-btn:hover{background:#E4EDF5;}
.viol-detail{margin-top:14px;}
table.viol-table{width:100%;border-collapse:collapse;font-size:var(--fs-small);}
table.viol-table th{text-align:left;font-size:var(--fs-caption);font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);padding:8px;border-bottom:1.5px solid var(--line);}
table.viol-table td{padding:9px 8px;border-bottom:1px solid var(--line);}
table.viol-table tr:last-child td{border-bottom:none;}
.month-chip{font-size:var(--fs-caption);background:var(--bg);color:#004C85;padding:3px 8px;border-radius:4px;font-weight:600;}

/* --- Modal drill-down --- */
.modal-backdrop{display:none;position:fixed;inset:0;background:rgba(27,39,51,0.5);z-index:100;align-items:center;justify-content:center;padding:20px;}
.modal-backdrop.open{display:flex;}
.modal-box{background:#fff;border-radius:12px;max-width:640px;width:100%;max-height:80vh;overflow:auto;}
.modal-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--line);position:sticky;top:0;background:#fff;}
.modal-head h3{margin:0;font-size:var(--fs-card-title);font-weight:600;}
.modal-close{border:none;background:none;font-size:18px;cursor:pointer;color:var(--muted);}
.modal-body{padding:18px 20px;}
.drill-note{font-size:var(--fs-caption);color:var(--faint);margin:0 0 14px;}

@media(max-width:768px){
  .wrap{padding:16px 16px 40px;}
  :root{
    --fs-dashboard-title: 22px;
    --fs-section-title: 19px;
    --fs-card-value: 34px;
  }
  .header-bar{flex-direction:column;align-items:stretch;}
  .header-title-block{margin-right:0;}
  .brand-title{white-space:normal;}
  .header-controls{width:100%;}
  #deptSelect{width:100%;}
  #monthSelect, #yearSelect{flex:1;width:auto;}
}
@media(max-width:480px){
  .header-controls{flex-wrap:nowrap;overflow-x:auto;gap:6px;padding-bottom:2px;-webkit-overflow-scrolling:touch;align-items:center;}
  .header-controls::-webkit-scrollbar{height:3px;}
  .header-controls > .selector-block{width:auto;flex:none;}
  #deptSelect{width:88px;}
  #monthSelect{width:70px;}
  #yearSelect{width:82px;}
  .header-controls .select-wrap select{padding:7px 20px 7px 7px;font-size:12px;}
  .header-btn-group{width:auto;flex:none;gap:6px;}
  .header-btn-group button{flex:none;padding:8px 10px;}
  .header-btn-group button .btn-text{display:none;}
}

@media print{
  .filter-row, .header-controls, .refresh-row, #refreshBtn, #printBtn, .viol-toggle-btn, .modal-backdrop{display:none !important;}
  .chart-grid{grid-template-columns:repeat(2,1fr) !important;}
  .trend-notes-grid{grid-template-columns:2fr 1fr !important;}
  .card, .kpi-card, .viol-card, .quicknote-card{break-inside:avoid;}
  body{background:#fff;}
}
"""

html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard tuân thủ quy trình - quy định</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>{chartjs_code}</script>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="header-bar">
    <div class="header-title-block">
      <p class="brand-eyebrow">Công tác Quản lý chất lượng</p>
      <h1 class="brand-title"><span class="title-full">Dashboard tuân thủ quy trình - quy định</span><span class="title-short">Dashboard tuân thủ QT-QĐ</span></h1>
    </div>
    <div class="header-controls">
      <div class="selector-block">
        <div class="select-wrap"><select id="deptSelect"><option>Đang tải danh sách...</option></select></div>
      </div>
      <div class="selector-block">
        <div class="select-wrap"><select id="monthSelect"></select></div>
      </div>
      <div class="selector-block">
        <div class="select-wrap"><select id="yearSelect"></select></div>
      </div>
      <div class="header-btn-group">
        <button id="refreshBtn">↻ <span class="btn-text">Làm mới</span></button>
        <button id="printBtn" class="btn-secondary">🖨 <span class="btn-text">Xuất PDF</span></button>
      </div>
    </div>
  </div>

  <div id="statusMsg" class="status"></div>
  <div class="unit-strip" style="display:none"><div class="unit-name">Đơn vị: <span id="unitNameOut">—</span></div></div>

  <h2 class="section-title"><span class="num">01</span>Tổng quan</h2>
  <div class="kpi-grid" id="kpiGrid"></div>

  <h2 class="section-title"><span class="num">02</span>Chi tiết từng nội dung giám sát</h2>
  <div class="trend-notes-grid" id="trendRow"></div>
  <div class="chart-grid" id="chartGrid"></div>

  <h2 class="section-title"><span class="num">03</span>Ghi chú giám sát</h2>
  <div class="viol-card" id="violCard"></div>
</div>

<div id="drillModal" class="modal-backdrop">
  <div class="modal-box">
    <div class="modal-head">
      <h3 id="drillModalTitle">Chi tiết tiêu chí</h3>
      <button id="drillModalClose" class="modal-close">✕</button>
    </div>
    <div id="drillModalBody" class="modal-body"></div>
  </div>
</div>
<script>
window.__CSV_URLS__ = {{
  detail: "{CSV_URL_DETAIL}",
  aggregate: "{CSV_URL_AGGREGATE}",
  violations: "{CSV_URL_VIOLATIONS}"
}};
{APP_JS}
boot(window.__CSV_URLS__);
</script>
</body>
</html>
"""

with open('/mnt/user-data/outputs/dashboard_live.html','w',encoding='utf-8') as f:
    f.write(html)
print("done", len(html))
