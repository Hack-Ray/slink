function router() {
    const hash = location.hash.replace(/^#\/?/, '');
    if (!hash || hash === '' || hash === '/') {
        renderHome();
    } else if (hash.startsWith('stats/')) {
        const code = hash.split('/')[1];
        renderStats(code);
    } else {
        renderNotFound();
    }
}

function renderHome() {
    document.getElementById('app').innerHTML = `
        <div class="container mt-5" style="max-width: 540px;">
            <div class="card shadow-sm border-0 rounded-4">
                <div class="card-body p-5">
                    <h1 class="text-center mb-3 fw-bold" style="font-size:2.2rem;letter-spacing:-1px;">Slink URL Shortener</h1>
                    <p class="text-center mb-4 text-muted">提供簡單快速的短網址服務</p>
                    <form id="shortenForm" class="mb-4">
                        <div class="mb-3">
                            <input type="url" class="form-control form-control-lg rounded-3" id="url" name="url" placeholder="請輸入要縮短的網址" required style="font-size:1.1rem;">
                        </div>
                        <button type="submit" class="btn btn-dark w-100 rounded-3 fw-semibold" style="font-size:1.1rem;">生成短網址</button>
                    </form>
                    <div id="result" class="d-none mb-4">
                        <div class="alert alert-success rounded-3">
                            <h5 class="fw-bold mb-2">短網址已生成：</h5>
                            <div class="d-flex align-items-center gap-2">
                                <input type="text" id="shortUrl" class="form-control me-2 rounded-2" readonly style="background:#f6f8fa;">
                                <button class="btn btn-outline-dark btn-sm rounded-2" id="copyBtn">複製</button>
                            </div>
                            <div class="mt-2">
                                <a href="#" id="statsLink" class="link-secondary text-decoration-none">查看統計</a>
                            </div>
                        </div>
                    </div>
                    <hr class="my-4">
                    <div class="mt-4">
                        <h5 class="fw-semibold mb-3">查詢短網址統計</h5>
                        <div class="input-group mb-3">
                            <input type="text" id="stats-code" class="form-control rounded-start-3" placeholder="請輸入短網址或代碼" style="background:#f6f8fa;">
                            <button class="btn btn-outline-dark rounded-end-3" type="button" id="stats-btn">查詢統計</button>
                        </div>
                    </div>
                </div>
            </div>
            <footer class="text-center text-muted mt-5" style="font-size:0.95rem;">Slink &copy; 2024</footer>
        </div>
    `;

    document.getElementById('shortenForm').onsubmit = async (e) => {
        e.preventDefault();
        const url = document.getElementById('url').value;
        try {
            const res = await fetch('/api/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ original_url: url })
            });
            const data = await res.json();
            if (res.ok) {
                document.getElementById('result').classList.remove('d-none');
                const shortUrl = `${window.location.origin}/${data.short_code}`;
                document.getElementById('shortUrl').value = shortUrl;
                document.getElementById('statsLink').href = `#/stats/${data.short_code}`;
                document.getElementById('statsLink').onclick = (e) => {
                    e.preventDefault();
                    location.hash = `#/stats/${data.short_code}`;
                };
                document.getElementById('copyBtn').onclick = () => {
                    const shortUrlInput = document.getElementById('shortUrl');
                    shortUrlInput.select();
                    document.execCommand('copy');
                    alert('已複製到剪貼簿');
                };
            } else {
                alert(data.detail || '產生失敗');
            }
        } catch {
            alert('發生錯誤，請稍後再試');
        }
    };

    document.getElementById('stats-btn').onclick = () => {
        let code = document.getElementById('stats-code').value.trim();
        if (!code) return alert('請輸入短網址或代碼');
        if (code.includes('/')) code = code.split('/').pop();
        location.hash = `#/stats/${code}`;
    };
}

async function renderStats(code) {
    document.getElementById('app').innerHTML = `
        <div class="container mt-5" style="max-width: 540px;">
            <div class="card shadow-sm border-0 rounded-4">
                <div class="card-body p-5">
                    <a href="#/" class="btn btn-link mb-3 px-0" style="color:#57606a;">&larr; 回首頁</a>
                    <h2 class="mb-4 fw-bold" style="font-size:1.6rem;">短網址統計</h2>
                    <div id="stats-loading" class="text-center text-muted mb-4">載入中...</div>
                    <canvas id="statsChart" height="120" class="rounded-3 border" style="background:#f6f8fa;"></canvas>
                </div>
            </div>
            <footer class="text-center text-muted mt-5" style="font-size:0.95rem;">Slink &copy; 2024</footer>
        </div>
    `;
    try {
        const res = await fetch(`/api/stats/${code}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || '查詢失敗');
        document.getElementById('stats-loading').remove();
        const clicks = data.clicks || {};
        const dates = Object.keys(clicks).sort();
        const values = dates.map(date => clicks[date]);
        const ctx = document.getElementById('statsChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: '點擊次數',
                    data: values,
                    backgroundColor: 'rgba(36, 41, 46, 0.7)'
                }]
            },
            options: {
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, stepSize: 1 }
                }
            }
        });
    } catch (e) {
        document.getElementById('stats-loading').textContent = e.message;
    }
}

function renderNotFound() {
    document.getElementById('app').innerHTML = `
        <div class="container mt-5 text-center">
            <div class="card shadow-sm border-0 rounded-4 p-5 d-inline-block">
                <h2 class="fw-bold mb-3">找不到頁面</h2>
                <a href="#/" class="btn btn-dark rounded-3 px-4">回首頁</a>
            </div>
            <footer class="text-center text-muted mt-5" style="font-size:0.95rem;">Slink &copy; 2024</footer>
        </div>
    `;
}

window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', router); 