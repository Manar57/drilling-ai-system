// ============================================
// USER AUTHENTICATION & DATABASE
// ============================================

let currentUser = null;

async function checkAuth() {
    try {
        const response = await fetch('/api/check_auth');
        const data = await response.json();
        
        if (data.authenticated) {
            currentUser = data;
            const userBar = document.getElementById('userBar');
            if (userBar) {
                userBar.style.display = 'flex';
                document.getElementById('usernameDisplay').textContent = data.username;
            }
            
            // Load user stats
            const statsResponse = await fetch('/api/user_stats');
            const statsData = await statsResponse.json();
            if (statsData.success && document.getElementById('userStats')) {
                document.getElementById('userStats').innerHTML = `${statsData.stats.total} classifications | Avg: ${statsData.stats.avg_confidence}%`;
            }
        } else {
            // window.location.href = 'login.html';
            window.location.href = '/';
        }
    } catch (error) {
        // window.location.href = 'login.html';
        window.location.href = '/';
    }
}

async function handleLogout() {
    await fetch('/api/logout', { method: 'POST' });
    // window.location.href = 'login.html';
    window.location.href = '/';
}

async function saveClassificationToDatabase(data, responseTime, depth, wob, rop) {
    try {
        await fetch('/api/save_classification', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_name: currentImageFile?.name || 'unknown',
                lithology: data.rockType,
                confidence: data.confidence,
                color: data.color,
                grain_size: data.grainSize,
                angularity: data.angularity,
                depth: depth || null,
                wob: wob || null,
                rop: rop || null,
                response_time: responseTime
            })
        });
    } catch (error) {
        console.error('Failed to save classification:', error);
    }
}

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewArea = document.getElementById('previewArea');
const previewImage = document.getElementById('previewImage');
const changeImageBtn = document.getElementById('changeImageBtn');
const classifyBtn = document.getElementById('classifyBtn');
const resultsSection = document.getElementById('resultsSection');
const performanceCard = document.getElementById('performanceCard');
const responseTimeValue = document.getElementById('responseTimeValue');
const avgResponseTimeValue = document.getElementById('avgResponseTimeValue');

let responseTimes = [];
let currentImageFile = null;

// Input elements
const depthInput = document.getElementById('depthInput');
const wobInput = document.getElementById('wobInput');
const ropInput = document.getElementById('ropInput');

// Summary elements
const summaryDepth = document.getElementById('summaryDepth');
const summaryWob = document.getElementById('summaryWob');
const summaryRop = document.getElementById('summaryRop');

// API URL (Flask server)
const API_URL = 'http://127.0.0.1:5000/predict';


function checkInputs() {
    const hasImage = currentImageFile !== null;
    classifyBtn.disabled = !hasImage;
}

function showPreview(file) {
    currentImageFile = file;
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        previewImage.dataset.dataurl = e.target.result;
        uploadArea.style.display = 'none';
        previewArea.style.display = 'block';
        checkInputs();
        
        resultsSection.style.display = 'none';
        document.getElementById('pdfCard').style.display = 'none';
        performanceCard.style.display = 'none';
    };
    reader.readAsDataURL(file);
}


async function classifyWithModel() {
    if (!currentUser) {
        alert('Please login first');
        return;
    }
    
    const t0 = performance.now();
    
    const depth = depthInput.value || null;
    const wob = wobInput.value || null;
    const rop = ropInput.value || null;
    
    summaryDepth.textContent = depth ? `${depth} m` : 'N/A';
    summaryWob.textContent = wob ? `${wob} klbf` : 'N/A';
    summaryRop.textContent = rop ? `${rop} m/hr` : 'N/A';
    
    const formData = new FormData();
    // formData.append('image', currentImageFile);
    formData.append('image', currentImageFile, currentImageFile.name);
    if (depth) formData.append('depth', depth);
    if (wob) formData.append('wob', wob);
    if (rop) formData.append('rop', rop);
 
    try {
        classifyBtn.disabled = true;
        classifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Processing...</span>';
        
        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI with results
            document.getElementById('rockType').textContent = data.rockType;
            document.getElementById('confidenceFill').style.width = data.confidence + '%';
            document.getElementById('confidenceValue').textContent = data.confidence + '%';
            document.getElementById('colorProp').textContent = data.color;
            document.getElementById('grainSizeProp').textContent = data.grainSize;
            document.getElementById('angularityProp').textContent = data.angularity;
            
            // Update probabilities
            const probabilitiesList = document.getElementById('probabilitiesList');
            probabilitiesList.innerHTML = '';
            data.probabilities.forEach(prob => {
                const item = document.createElement('div');
                item.className = 'probability-item';
                item.innerHTML = `
                    <span class="probability-name">${prob.name}</span>
                    <div class="probability-bar">
                        <div class="probability-fill" style="width: ${prob.value}%"></div>
                    </div>
                    <span class="probability-value">${prob.value}%</span>
                `;
                probabilitiesList.appendChild(item);
            });
            
            window.currentDescription = data.description;
            
            resultsSection.style.display = 'flex';
            document.getElementById('pdfCard').style.display = 'block';
            
            const t1 = performance.now();
            const rt = Math.round(t1 - t0);
            responseTimes.push(rt);
            if (responseTimes.length > 5) responseTimes.shift();
            const avg = Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length);
            
            responseTimeValue.textContent = rt;
            avgResponseTimeValue.textContent = avg;
            performanceCard.style.display = 'block';
            
            // Save to database
            await saveClassificationToDatabase(data, rt, depth, wob, rop);
            
            // Refresh stats
            const statsResponse = await fetch('/api/user_stats');
            const statsData = await statsResponse.json();
            if (statsData.success && document.getElementById('userStats')) {
                document.getElementById('userStats').innerHTML = `${statsData.stats.total} classifications | Avg: ${statsData.stats.avg_confidence}%`;
            }
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('API Error:', error);
        alert('Error connecting to classification server. Make sure Flask is running on port 5000.\n\n' + error.message);
    } finally {
        classifyBtn.disabled = false;
        classifyBtn.innerHTML = '<i class="fas fa-robot"></i><span>Run Classification</span>';
        checkInputs();
    }
}

// ============================================
// PDF Download
// ============================================
function downloadPDF() {
    const safeText = (value, fallback = '—') => {
        if (value === null || value === undefined) return fallback;
        const str = String(value).trim();
        return str.length ? str : fallback;
    };
    
    const getElementText = (id, fallback = '—') => {
        const el = document.getElementById(id);
        return el ? safeText(el.textContent, fallback) : fallback;
    };
    
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const reportId = `RPT-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
    
    const depth = depthInput.value || '0';
    const wob = wobInput.value || '0';
    const rop = ropInput.value || '0';
    
    const rockType = getElementText('rockType', 'Unknown');
    const confidence = getElementText('confidenceValue', '0%');
    const color = getElementText('colorProp', '—');
    const grainSize = getElementText('grainSizeProp', '—');
    const angularity = getElementText('angularityProp', '—');
    
    const description = window.currentDescription || 'Lithology classification based on AI model prediction.';
    
    const probabilityItems = Array.from(document.querySelectorAll('.probability-item')).map(item => {
        const nameEl = item.querySelector('.probability-name');
        const valueEl = item.querySelector('.probability-value');
        const name = nameEl ? safeText(nameEl.textContent) : 'Unknown';
        const valueText = valueEl ? safeText(valueEl.textContent, '0%') : '0%';
        const valueNum = parseFloat(String(valueText).replace('%', '')) || 0;
        return { name, valueText, valueNum };
    });
    
    let imageHTML = '';
    const dataUrl = previewImage?.dataset?.dataurl;
    if (dataUrl && dataUrl.startsWith('data:image')) {
        imageHTML = `
            <div style="text-align: center; margin: 0 0 25px 0;">
                <img src="${dataUrl}" style="max-width: 280px; max-height: 180px; border-radius: 8px; border: 2px solid #2563eb; padding: 4px;">
                <p style="color: #64748b; font-size: 0.85rem; margin: 6px 0 0 0;">Rock Sample Image</p>
            </div>
        `;
    }
    
    let recommendations = '';
    if (rockType === 'Sandstone') {
        recommendations = `
            <li>Moderate to good penetration expected; maintain stable WOB and monitor vibration.</li>
            <li>Monitor for potential fluid loss if sandstone is highly porous.</li>
            <li>Check returns for signs of lost circulation or high cuttings volume.</li>
        `;
    } else if (rockType === 'Limestone') {
        recommendations = `
            <li>Lower ROP is expected; optimize WOB and RPM carefully to avoid bit damage.</li>
            <li>Monitor bit wear; limestone may be abrasive depending on cementation.</li>
            <li>Watch for fractures/vugs that could cause losses.</li>
        `;
    } else if (rockType === 'Shale') {
        recommendations = `
            <li>Watch for hole instability; consider optimizing mud properties to reduce swelling/cavings.</li>
            <li>Monitor torque/drag and adjust ROP if signs of stick-slip appear.</li>
            <li>Inspect cuttings frequently for sloughing indicators.</li>
        `;
    } else {
        recommendations = `
            <li>Inputs appear outside the defined ranges; verify units and values.</li>
            <li>Consider manual inspection (mud logger) for confirmation.</li>
            <li>Re-run prediction with a clearer image and accurate drilling parameters.</li>
        `;
    }
    
    const element = document.createElement('div');
    element.innerHTML = `
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 30px 35px; background: white; color: #1e293b;">
            <div style="background: linear-gradient(145deg, #1e293b, #0f172a); color: white; padding: 25px 20px; border-radius: 12px; margin: 0 0 20px 0; text-align: center;">
                <h1 style="font-size: 1.9rem; margin: 0 0 6px 0;">Drilling Cuttings Classification Report</h1>
                <p style="font-size: 1rem; margin: 0 0 12px 0;">AI-Powered Lithology Identification System</p>
                <div style="display: flex; justify-content: center; gap: 18px; font-size: 0.9rem;">
                    <span>📅 ${dateStr}</span>
                    <span>⏱️ ${timeStr}</span>
                </div>
            </div>
            
            <div style="text-align: right; margin: 0 0 18px 0; color: #475569; font-size: 0.85rem; border-bottom: 1px solid #e2e8f0; padding: 0 0 8px 0;">
                <strong style="color: #2563eb;">Report ID:</strong> ${reportId}
            </div>
            
            ${imageHTML}
            
            <div style="margin: 0 0 22px 0;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding: 0 0 6px 0; font-size: 1.35rem;">1. Classification Result</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; background: #f8fafc; padding: 16px; border-radius: 10px;">
                    <div><div style="color: #475569;">Lithology</div><div style="font-size: 1.8rem; font-weight: 700; color: #2563eb;">${rockType}</div></div>
                    <div><div style="color: #475569;">Confidence Level</div><div style="font-size: 1.8rem; font-weight: 700; color: #059669;">${confidence}</div></div>
                </div>
            </div>
            
            <div style="margin: 0 0 22px 0;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding: 0 0 6px 0; font-size: 1.35rem;">2. Drilling Parameters</h2>
                <table style="width: 100%; border-collapse: collapse; background: #f8fafc;">
                    <tr style="background: #e2e8f0;"><th style="padding: 10px; text-align: left;">Parameter</th><th style="padding: 10px; text-align: left;">Value</th></tr>
                    <tr><td style="padding: 10px;">DEPTH</td><td style="padding: 10px;">${depth} m</td></tr>
                    <tr><td style="padding: 10px;">WEIGHT ON BIT</td><td style="padding: 10px;">${wob} klbf</td></tr>
                    <tr><td style="padding: 10px;">RATE OF PENETRATION</td><td style="padding: 10px;">${rop} m/hr</td></tr>
                </table>
            </div>
            
            <div style="margin: 0 0 22px 0;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding: 0 0 6px 0; font-size: 1.35rem;">3. Rock Properties</h2>
                <table style="width: 100%; border-collapse: collapse; background: #f8fafc;">
                    <tr style="background: #e2e8f0;"><th style="padding: 10px; text-align: left;">Property</th><th style="padding: 10px; text-align: left;">Value</th></tr>
                    <tr><td style="padding: 10px;">COLOR</td><td style="padding: 10px;">${color}</td></tr>
                    <tr><td style="padding: 10px;">GRAIN SIZE</td><td style="padding: 10px;">${grainSize}</td></tr>
                    <tr><td style="padding: 10px;">ANGULARITY</td><td style="padding: 10px;">${angularity}</td></tr>
                </table>
            </div>
            
            <div style="margin: 0 0 22px 0;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding: 0 0 6px 0; font-size: 1.35rem;">4. Geological Description</h2>
                <div style="background: #f0f9ff; padding: 14px 16px; border-radius: 8px; border-left: 4px solid #2563eb;">
                    <p style="margin: 0;">${description}</p>
                </div>
            </div>
            
            <div style="margin: 0 0 22px 0;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding: 0 0 6px 0; font-size: 1.35rem;">5. Probability Distribution</h2>
                ${probabilityItems.map(p => `
                    <div style="margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between;"><span>${p.name}</span><span style="font-weight: 600; color: #2563eb;">${p.valueText}</span></div>
                        <div style="background: #e2e8f0; height: 8px; border-radius: 4px; margin-top: 4px;"><div style="width: ${p.valueNum}%; background: #2563eb; height: 8px; border-radius: 4px;"></div></div>
                    </div>
                `).join('')}
            </div>
            
            <div style="margin: 0 0 22px 0;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding: 0 0 6px 0; font-size: 1.35rem;">6. Drilling Recommendations</h2>
                <div style="background: #f8fafc; padding: 14px 18px; border-radius: 8px;"><ul style="margin: 0; padding-left: 18px;">${recommendations}</ul></div>
            </div>
            
            <div style="margin: 25px 0 0 0; text-align: center; color: #64748b; font-size: 0.8rem; border-top: 2px solid #e2e8f0; padding: 16px 0 0 0;">
                <div><strong>Team F005</strong> | PETE · CHE · CS · ISE | Senior Design Project</div>
                <div>Automatic Classification of Drilling Particles Using AI Data-Driven Techniques</div>
                <div style="color: #2563eb;">Term #252 | Final Design Report</div>
            </div>
        </div>
    `;
    
    const opt = {
        margin: [0.4, 0.4, 0.4, 0.4],
        filename: `Drilling_Cuttings_Report_${rockType}_${now.toISOString().slice(0,10)}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(element).save();
}

// ============================================
// Event Listeners
// ============================================
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        showPreview(file);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) showPreview(e.target.files[0]);
});

changeImageBtn.addEventListener('click', () => {
    uploadArea.style.display = 'block';
    previewArea.style.display = 'none';
    currentImageFile = null;
    fileInput.value = '';
    checkInputs();
    resultsSection.style.display = 'none';
    document.getElementById('pdfCard').style.display = 'none';
    performanceCard.style.display = 'none';
    responseTimeValue.textContent = '—';
    avgResponseTimeValue.textContent = '—';
    responseTimes = [];
});

[depthInput, wobInput, ropInput].forEach(input => {
    input.addEventListener('input', checkInputs);
});

classifyBtn.addEventListener('click', classifyWithModel);
document.getElementById('downloadPdfBtn').addEventListener('click', downloadPDF);

// Initial check - redirect to login if not authenticated
checkAuth();