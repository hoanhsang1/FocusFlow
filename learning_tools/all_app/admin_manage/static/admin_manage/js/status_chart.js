// status_chart.js
class StatusChart {
    constructor(options = {}) {
        this.options = {
            canvasId: options.canvasId || 'statusChart',                    // ID của thẻ <canvas>
            containerId: options.containerId || 'statusChartContainer',     // ID container chứa biểu đồ
            legendId: options.legendId || 'statusChartLegend',              // ID phần tử hiển thị chú thích
            statsId: options.statsId || 'statusChartStats',                 // ID phần tử hiển thị thống kê
            loadingId: options.loadingId || 'statusChartLoading',           // ID loading indicator
            errorId: options.errorId || 'statusChartError',                 // ID thông báo lỗi
            chartData: options.chartData || null,                           // Dữ liệu biểu đồ
            ...options
        };
        
        this.chart = null;                                                   //Lưu trữ instance của Chart.js
        this.currentChartType = 'bar';                                      //chọn loại biểu đồ doughnut,bar,pie,line
        
        this.colorPalette = [
            '#36a2eb', '#ff6384', '#4bc0c0', '#ff9f40', '#9966ff',  // danh sách màu của biểu đồ
            '#ffcd56', '#c9cbcf', '#4dc9f6', '#f67019', '#537bc4'
        ];
        
        this.init();  //Gọi phương thức khởi tạo ngay sau khi tạo instance
    }       
    
    // phương thức khời tạo
    init() {
        if (!this.validateOptions()) {
            return;
        }
        this.setupEventListeners();
        this.initializeChart();
    }
    
    // phương thức kiểm tra có data hay k
    validateOptions() {
        if (!this.options.chartData) {
            console.error('StatusChart: No chart data provided');
            this.showError('No chart data available');
            return false;
        }
        
        if (!this.options.chartData.labels || !this.options.chartData.data) {
            console.error('StatusChart: Invalid chart data format');
            this.showError('Invalid chart data format');
            return false;
        }
        
        return true;
    }
    
    setupEventListeners() {
        // Chart type buttons
        document.querySelectorAll('[id^="chartType"]').forEach(btn => {
            const type = btn.id.replace('chartType', '').toLowerCase();
            if (['doughnut', 'pie', 'bar'].includes(type)) {
                btn.addEventListener('click', () => this.setChartType(type));
            }
        });
        
        // Export button
        const exportBtn = document.getElementById('exportChartBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportChart());
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshChartBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshChart());
        }
    }
    
    // phương thức cập nhậy biểu đồ
    initializeChart() {
        const canvas = document.getElementById(this.options.canvasId); // tìm thẻ canvas
        if (!canvas) {
            console.error(`StatusChart: Canvas element with id '${this.options.canvasId}' not found`);
            return;
        }
        
        // Ẩn loading indicator
        this.showLoading(false);
        
        const ctx = canvas.getContext('2d');  //2d là vẽ biễu đồ dạng 2d
        
        // Prepare data
        const chartConfig = this.prepareChartData(); // để cấu hình dữ liệu theo định dạng của Chart.js.
        
        // Chart options
        const chartOptions = this.getChartOptions(); // để lấy cấu hình hiển thị (tooltip, trục, cutout).
        
        // Create or update chart
        if (this.chart) {
            this.chart.destroy();  // xoá biểu đồ cũ
        }
        
        try {
            this.chart = new Chart(ctx, {  // tạo biểu đồ ms
                type: this.currentChartType,
                data: chartConfig,
                options: chartOptions
            });
            
            console.log('✅ Chart created successfully');
            
            // Update legend and stats
            this.updateLegend();  
            this.updateStats();
        } catch (error) {
            console.error('❌ Error creating chart:', error);
            this.showError('Failed to create chart: ' + error.message);
        }
    }
    
    // XỬ LÝ DỮ LIỆU ĐỂ PHÙ HỢP VỚI CHART.JS
    prepareChartData() {
        const labels = this.options.chartData.labels || [];
        const data = this.options.chartData.data || [];
        
        // Assign colors
        const backgroundColors = labels.map((_, index) => {
            return this.colorPalette[index % this.colorPalette.length];    //gám màu sắc
        });
        
        return {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: '#ffffff',
                borderWidth: 2,
                hoverOffset: this.currentChartType === 'bar' ? 4 : 15,
                borderRadius: this.currentChartType === 'bar' ? 4 : 0
            }]
        };
    }
    
    getChartOptions() {
        const isBarChart = this.currentChartType === 'bar';
        
        return {
            responsive: true,                   //co giãn theo kích thước container.
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false  // tắt chú thích mặc định
                },
                tooltip: {
                    //giúp hiển thị thông tin chi tiết trong tooltip dưới dạng: Tên trạng thái: Giá trị tasks (Phần trăm%).
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    padding: 12,
                    cornerRadius: 6,
                    callbacks: {
                        label: (context) => {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} tasks (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: !isBarChart ? '60%' : '0%', // Xác định kích thước lỗ cắt ở giữa. Nó được đặt là '60%' nếu là Doughnut/Pie, và '0%' nếu là Bar.
            scales: isBarChart ? {              // các cấu hình cho trục X và Y (ví dụ: beginAtZero: true, tiêu đề trục).
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Number of Tasks',
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Status',
                        font: {
                            size: 12
                        }
                    }
                }
            } : undefined
        };
    }
    
    updateLegend() {
        const legendContainer = document.getElementById(this.options.legendId);
        if (!legendContainer) return;
        
        const labels = this.options.chartData.labels || [];
        const data = this.options.chartData.data || [];
        const total = data.reduce((sum, value) => sum + value, 0); //tính phần trăm
        
        let html = '';
        
        labels.forEach((label, index) => {
            const value = data[index] || 0;
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
            const color = this.colorPalette[index % this.colorPalette.length];
            const isHidden = this.chart?.getDatasetMeta(0)?.data[index]?.hidden || false;
            
            html += `
                <div class="status-legend-item ${isHidden ? 'hidden' : ''}" 
                     data-index="${index}"
                     onclick="window.statusChartInstance.toggleDataset(${index})">
                    <div class="status-legend-color" style="background-color: ${color};"></div>
                    <span class="status-legend-text">${label}</span>
                    <span class="status-legend-value">${value} (${percentage}%)</span>
                </div>
            `;
        });
        
        legendContainer.innerHTML = html;
    }
    
    updateStats() {
        const statsContainer = document.getElementById(this.options.statsId);
        if (!statsContainer) return;
        
        const data = this.options.chartData.data || [];
        const total = data.reduce((sum, value) => sum + value, 0);
        
        // Find max and min
        const maxValue = Math.max(...data);
        const minValue = Math.min(...data.filter(v => v > 0));
        const maxIndex = data.indexOf(maxValue);
        const minIndex = data.indexOf(minValue);
        const labels = this.options.chartData.labels || [];
        
        const maxLabel = labels[maxIndex] || 'N/A';
        const minLabel = labels[minIndex] || 'N/A';
        
        statsContainer.innerHTML = `
            <div class="status-chart-total">
                <i class="fas fa-tasks"></i> Total: ${total} tasks
            </div>
            <div class="status-chart-percentage">
                <span title="Highest: ${maxLabel} (${maxValue})">
                    <i class="fas fa-arrow-up" style="color: #28a745;"></i> Max: ${maxValue}
                </span>
                <span style="margin-left: 10px;" title="Lowest: ${minLabel} (${minValue})">
                    <i class="fas fa-arrow-down" style="color: #dc3545;"></i> Min: ${minValue}
                </span>
            </div>
        `;
    }
    
    setChartType(type) {
        if (['doughnut', 'pie', 'bar'].includes(type)) {
            this.currentChartType = type;
            this.initializeChart();
        }
    }
    
    toggleDataset(index) {
        if (!this.chart) return;
        
        const meta = this.chart.getDatasetMeta(0);
        if (meta.data[index]) {
            meta.data[index].hidden = !meta.data[index].hidden;
            this.chart.update();
            this.updateLegend();
        }
    }
    
    exportChart() {
        if (!this.chart) return;
        
        const canvas = document.getElementById(this.options.canvasId);
        if (!canvas) return;
        
        const link = document.createElement('a');
        const date = new Date().toISOString().slice(0, 10);
        const typeName = this.currentChartType.charAt(0).toUpperCase() + this.currentChartType.slice(1);
        link.download = `task-status-${typeName}-${date}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }
    
    refreshChart() {
        this.showLoading(true);
        
        // Simulate API call delay
        setTimeout(() => {
            this.initializeChart();
            this.showLoading(false);
            this.showNotification('Chart data refreshed', 'success');
        }, 500);
    }
    
    showLoading(show) {
        const loadingEl = document.getElementById(this.options.loadingId);
        if (loadingEl) {
            loadingEl.style.display = show ? 'flex' : 'none';
        }
    }
    
    showError(message) {
        const errorEl = document.getElementById(this.options.errorId);
        if (errorEl) {
            errorEl.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            `;
            errorEl.style.display = 'block';
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `status-chart-notification status-chart-notification-${type}`;
        notification.innerHTML = `
            <div style="padding: 10px 15px; border-radius: 4px; background: ${
                type === 'error' ? '#f8d7da' : 
                type === 'success' ? '#d4edda' : '#d1ecf1'
            }; color: ${
                type === 'error' ? '#721c24' : 
                type === 'success' ? '#155724' : '#0c5460'
            }; margin-bottom: 10px;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                ${message}
            </div>
        `;
        
        const container = document.getElementById(this.options.containerId);
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Remove notification after 3 seconds
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }
    
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Hàm khởi tạo chart với retry mechanism
function initializeStatusChart() {
    console.log('=== INITIALIZING STATUS CHART ===');
    
    // Thử nhiều nguồn dữ liệu
    let chartData = null;
    let dataSource = '';
    
    // Nguồn 1: window.statusChartData
    if (window.statusChartData && window.statusChartData.labels && window.statusChartData.data) {
        chartData = window.statusChartData;
        dataSource = 'window.statusChartData';
    }
    // Nguồn 2: window.FocusFlowAnalytics.chartData
    else if (window.FocusFlowAnalytics && window.FocusFlowAnalytics.chartData && 
             window.FocusFlowAnalytics.chartData.labels && window.FocusFlowAnalytics.chartData.data) {
        chartData = window.FocusFlowAnalytics.chartData;
        dataSource = 'window.FocusFlowAnalytics.chartData';
    }
    // Nguồn 3: Data attribute từ container
    else {
        const container = document.getElementById('chartDataContainer');
        if (container) {
            try {
                const labels = JSON.parse(container.getAttribute('data-chart-labels') || '[]');
                const data = JSON.parse(container.getAttribute('data-chart-data') || '[]');
                if (labels.length > 0 && data.length > 0) {
                    chartData = { labels, data };
                    dataSource = 'data attributes';
                }
            } catch (e) {
                console.error('Error parsing data attributes:', e);
            }
        }
    }
    
    // Fallback data nếu không có dữ liệu
    if (!chartData) {
        console.warn('No chart data found, using fallback data');
        chartData = {
            labels: ['Pending', 'Completed', 'In Progress'],
            data: [13, 1, 2]
        };
        dataSource = 'fallback';
    }
    
    console.log(`✅ Using data from: ${dataSource}`, chartData);
    
    // Khởi tạo chart
    try {
        window.statusChartInstance = new StatusChart({
            chartData: chartData,
            canvasId: 'statusChart',
            containerId: 'chartDataContainer',
            legendId: 'statusChartLegend',
            statsId: 'statusChartStats',
            loadingId: 'statusChartLoading',
            errorId: 'statusChartError'
        });
        
        console.log('✅ StatusChart initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize StatusChart:', error);
        
        // Hiển thị thông báo lỗi
        const errorEl = document.getElementById('statusChartError');
        if (errorEl) {
            errorEl.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #dc3545;">
                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                    <p>Failed to load chart: ${error.message}</p>
                </div>
            `;
            errorEl.style.display = 'block';
        }
        
        // Ẩn loading
        const loadingEl = document.getElementById('statusChartLoading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
}

// Khởi tạo khi DOM sẵn sàng
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing chart...');
    
    // Đợi 300ms để đảm bảo tất cả script đã chạy
    setTimeout(initializeStatusChart, 300);
});

// Fallback nếu DOMContentLoaded đã chạy
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initializeStatusChart, 300);
}

// Global functions để có thể gọi từ console
window.refreshStatusChart = function() {
    if (window.statusChartInstance) {
        window.statusChartInstance.refreshChart();
    } else {
        initializeStatusChart();
    }
};

window.exportStatusChart = function() {
    if (window.statusChartInstance) {
        window.statusChartInstance.exportChart();
    }
};