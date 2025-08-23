/**
 * 移动端设备检测和 UI 优化模块
 * 
 * 功能：
 * - 检测移动设备类型
 * - 动态加载移动端优化样式
 * - 提供触摸友好的交互
 * - 移动端专用导航
 */

class MobileDetector {
    constructor() {
        this.userAgent = navigator.userAgent.toLowerCase();
        this.isMobile = this.detectMobile();
        this.isTablet = this.detectTablet();
        this.deviceType = this.getDeviceType();
        this.touchSupport = this.detectTouchSupport();
        
        // 初始化移动端优化
        this.init();
    }
    
    /**
     * 检测是否为移动设备 - 主要基于屏幕宽度
     */
    detectMobile() {
        // 主要判断条件：屏幕宽度
        const screenWidth = window.innerWidth;
        
        // 移动端宽度阈值：768px 及以下
        if (screenWidth <= 768) {
            return true;
        }
        
        // 辅助判断：User-Agent 中的移动设备关键词
        const mobileKeywords = [
            'mobile', 'android', 'iphone', 'ipod', 'blackberry', 
            'windows phone', 'opera mini', 'iemobile'
        ];
        
        // 如果屏幕宽度在 769-1024px 之间，且 User-Agent 包含移动关键词，也认为是移动设备
        if (screenWidth <= 1024 && mobileKeywords.some(keyword => this.userAgent.includes(keyword))) {
            return true;
        }
        
        return false;
    }
    
    /**
     * 检测是否为平板设备 - 主要基于屏幕宽度
     */
    detectTablet() {
        const screenWidth = window.innerWidth;
        
        // 平板宽度范围：769px - 1024px
        if (screenWidth > 768 && screenWidth <= 1024) {
            // 如果有触摸支持，更可能是平板
            if (this.touchSupport) {
                return true;
            }
            
            // 检查 User-Agent 中的平板关键词
            const tabletKeywords = ['ipad', 'tablet', 'kindle', 'playbook'];
            if (tabletKeywords.some(keyword => this.userAgent.includes(keyword))) {
                return true;
            }
        }
        
        // 特殊情况：iPad 可能报告更大的屏幕尺寸
        if (screenWidth > 1024 && this.userAgent.includes('ipad')) {
            return true;
        }
        
        return false;
    }
    
    /**
     * 检测触摸支持
     */
    detectTouchSupport() {
        return 'ontouchstart' in window || 
               navigator.maxTouchPoints > 0 || 
               navigator.msMaxTouchPoints > 0;
    }
    
    /**
     * 获取设备类型 - 基于屏幕宽度优先判断
     */
    getDeviceType() {
        const screenWidth = window.innerWidth;
        
        // 基于屏幕宽度的主要判断
        if (screenWidth <= 768) {
            return 'mobile';
        } else if (screenWidth <= 1024) {
            // 在平板范围内，进一步判断
            if (this.isTablet) {
                return 'tablet';
            }
            // 如果不是平板但在此范围内，可能是小屏笔记本，按桌面处理
            return 'desktop';
        } else {
            // 大屏幕设备
            return 'desktop';
        }
    }
    
    /**
     * 获取设备信息
     */
    getDeviceInfo() {
        const screenWidth = window.innerWidth;
        const screenHeight = window.innerHeight;
        
        return {
            isMobile: this.isMobile,
            isTablet: this.isTablet,
            deviceType: this.deviceType,
            touchSupport: this.touchSupport,
            screenWidth: screenWidth,
            screenHeight: screenHeight,
            screenSize: this.getScreenSizeCategory(screenWidth),
            aspectRatio: (screenWidth / screenHeight).toFixed(2),
            pixelRatio: window.devicePixelRatio || 1,
            userAgent: this.userAgent,
            orientation: this.getOrientation(),
            detectionMethod: this.getDetectionMethod(screenWidth)
        };
    }
    
    /**
     * 获取屏幕尺寸分类
     */
    getScreenSizeCategory(width) {
        if (width <= 480) return 'small-mobile';
        if (width <= 768) return 'mobile';
        if (width <= 1024) return 'tablet';
        if (width <= 1440) return 'desktop';
        return 'large-desktop';
    }
    
    /**
     * 获取检测方法说明
     */
    getDetectionMethod(width) {
        if (width <= 768) {
            return 'screen-width-mobile';
        } else if (width <= 1024) {
            if (this.touchSupport) {
                return 'screen-width-touch-tablet';
            } else {
                return 'screen-width-desktop';
            }
        } else {
            return 'screen-width-desktop';
        }
    }
    
    /**
     * 获取屏幕方向
     */
    getOrientation() {
        if (screen.orientation) {
            return screen.orientation.angle === 0 || screen.orientation.angle === 180 
                ? 'portrait' : 'landscape';
        }
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    }
    
    /**
     * 初始化移动端优化
     */
    init() {
        // 添加设备类型到 body 类名
        document.body.classList.add(`device-${this.deviceType}`);
        
        if (this.touchSupport) {
            document.body.classList.add('touch-device');
        }
        
        // 设置视口元标签（如果不存在）
        this.setupViewport();
        
        // 加载移动端样式
        if (this.isMobile || this.isTablet) {
            this.loadMobileStyles();
            this.setupMobileInteractions();
            this.setupMobileNavigation();
        }
        
        // 监听屏幕方向变化
        this.setupOrientationListener();
        
        // 监听窗口大小变化
        this.setupResizeListener();
        
        console.log('移动端检测完成:', this.getDeviceInfo());
    }
    
    /**
     * 设置视口元标签
     */
    setupViewport() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        // 移动端优化的视口设置
        if (this.isMobile) {
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        } else {
            viewport.content = 'width=device-width, initial-scale=1.0';
        }
    }
    
    /**
     * 加载移动端样式
     */
    loadMobileStyles() {
        const mobileCSS = document.createElement('style');
        mobileCSS.id = 'mobile-styles';
        mobileCSS.textContent = this.getMobileCSS();
        document.head.appendChild(mobileCSS);
    }
    
    /**
     * 获取移动端 CSS 样式
     */
    getMobileCSS() {
        return `
            /* 移动端基础样式 */
            .device-mobile body {
                font-size: 16px;
                line-height: 1.5;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }
            
            /* 触摸友好的按钮 */
            .touch-device button,
            .touch-device .btn,
            .touch-device input[type="submit"],
            .touch-device input[type="button"] {
                min-height: 44px;
                min-width: 44px;
                padding: 12px 20px;
                font-size: 16px;
                border-radius: 8px;
                cursor: pointer;
                -webkit-appearance: none;
                appearance: none;
            }
            
            /* 触摸友好的输入框 */
            .touch-device input,
            .touch-device select,
            .touch-device textarea {
                min-height: 44px;
                padding: 12px 16px;
                font-size: 16px;
                border-radius: 8px;
                -webkit-appearance: none;
                appearance: none;
            }
            
            /* 移动端导航 */
            .mobile-nav {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #fff;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                padding: 10px 15px;
                display: none;
            }
            
            .device-mobile .mobile-nav {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .mobile-nav-title {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            
            .mobile-nav-menu {
                background: none;
                border: none;
                font-size: 24px;
                color: #333;
                padding: 5px;
                cursor: pointer;
            }
            
            /* 移动端菜单 */
            .mobile-menu {
                position: fixed;
                top: 60px;
                left: 0;
                right: 0;
                background: #fff;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 999;
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease;
            }
            
            .mobile-menu.open {
                max-height: 400px;
            }
            
            .mobile-menu-item {
                display: block;
                padding: 15px 20px;
                color: #333;
                text-decoration: none;
                border-bottom: 1px solid #eee;
                font-size: 16px;
            }
            
            .mobile-menu-item:hover,
            .mobile-menu-item:active {
                background: #f8f9fa;
                color: #007bff;
            }
            
            /* 移动端内容区域 */
            .device-mobile .container,
            .device-mobile .main-content {
                padding-top: 70px;
                padding-left: 15px;
                padding-right: 15px;
            }
            
            /* 移动端表单优化 */
            .device-mobile .form-group {
                margin-bottom: 20px;
            }
            
            .device-mobile label {
                font-size: 16px;
                margin-bottom: 8px;
                display: block;
            }
            
            /* 移动端卡片样式 */
            .device-mobile .card,
            .device-mobile .voice-mode-section {
                margin-bottom: 15px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            /* 移动端按钮组 */
            .device-mobile .btn-group {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .device-mobile .btn-group button {
                width: 100%;
            }
            
            /* 移动端选择器优化 */
            .device-mobile select {
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
                background-position: right 12px center;
                background-repeat: no-repeat;
                background-size: 16px;
                padding-right: 40px;
            }
            
            /* 移动端文本区域 */
            .device-mobile textarea {
                resize: vertical;
                min-height: 120px;
            }
            
            /* 移动端反馈信息 */
            .device-mobile .feedback {
                font-size: 14px;
                padding: 8px 12px;
                border-radius: 6px;
                margin-top: 8px;
            }
            
            /* 移动端加载状态 */
            .device-mobile .loading {
                position: relative;
            }
            
            .device-mobile .loading::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 20px;
                height: 20px;
                margin: -10px 0 0 -10px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* 平板设备样式 */
            .device-tablet .container {
                max-width: 900px;
                padding: 20px 30px;
            }
            
            .device-tablet .btn-group {
                display: flex;
                flex-direction: row;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            /* 横屏优化 */
            @media (orientation: landscape) {
                .device-mobile .mobile-nav {
                    padding: 8px 15px;
                }
                
                .device-mobile .container {
                    padding-top: 60px;
                }
                
                .device-mobile .mobile-menu {
                    top: 50px;
                }
            }
            
            /* 小屏幕优化 */
            @media (max-width: 480px) {
                .device-mobile body {
                    font-size: 14px;
                }
                
                .device-mobile .mobile-nav-title {
                    font-size: 16px;
                }
                
                .device-mobile .container {
                    padding-left: 10px;
                    padding-right: 10px;
                }
            }
            
            /* 触摸反馈 */
            .touch-device button:active,
            .touch-device .btn:active,
            .touch-device .mobile-menu-item:active {
                transform: scale(0.98);
                transition: transform 0.1s ease;
            }
            
            /* 禁用悬停效果在触摸设备上 */
            @media (hover: none) {
                .touch-device *:hover {
                    background-color: initial;
                    color: initial;
                }
            }
        `;
    }
    
    /**
     * 设置移动端交互
     */
    setupMobileInteractions() {
        // 添加触摸事件支持
        if (this.touchSupport) {
            this.setupTouchEvents();
        }
        
        // 优化表单交互
        this.optimizeFormInteractions();
        
        // 添加双击缩放禁用（在需要的地方）
        this.setupZoomControl();
    }
    
    /**
     * 设置触摸事件
     */
    setupTouchEvents() {
        // 为按钮添加触摸反馈
        document.addEventListener('touchstart', (e) => {
            if (e.target.matches('button, .btn, input[type="submit"], input[type="button"]')) {
                e.target.classList.add('touch-active');
            }
        });
        
        document.addEventListener('touchend', (e) => {
            if (e.target.matches('button, .btn, input[type="submit"], input[type="button"]')) {
                setTimeout(() => {
                    e.target.classList.remove('touch-active');
                }, 150);
            }
        });
        
        // 添加触摸滑动支持（如果需要）
        this.setupSwipeGestures();
    }
    
    /**
     * 设置滑动手势
     */
    setupSwipeGestures() {
        let startX, startY, startTime;
        
        document.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            startTime = Date.now();
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const touch = e.changedTouches[0];
            const endX = touch.clientX;
            const endY = touch.clientY;
            const endTime = Date.now();
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            const deltaTime = endTime - startTime;
            
            // 检测快速滑动
            if (deltaTime < 300 && Math.abs(deltaX) > 50 && Math.abs(deltaY) < 100) {
                const direction = deltaX > 0 ? 'right' : 'left';
                this.handleSwipe(direction, e.target);
            }
            
            startX = startY = null;
        });
    }
    
    /**
     * 处理滑动事件
     */
    handleSwipe(direction, target) {
        // 可以在这里添加滑动处理逻辑
        // 例如：切换标签页、打开/关闭菜单等
        console.log(`滑动方向: ${direction}`, target);
        
        // 触发自定义事件
        const swipeEvent = new CustomEvent('swipe', {
            detail: { direction, target }
        });
        document.dispatchEvent(swipeEvent);
    }
    
    /**
     * 优化表单交互
     */
    optimizeFormInteractions() {
        // 自动聚焦优化
        document.addEventListener('focusin', (e) => {
            if (this.isMobile && e.target.matches('input, textarea, select')) {
                // 滚动到输入框
                setTimeout(() => {
                    e.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            }
        });
        
        // 输入框类型优化
        this.optimizeInputTypes();
    }
    
    /**
     * 优化输入框类型
     */
    optimizeInputTypes() {
        // 为数字输入添加数字键盘
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.setAttribute('inputmode', 'numeric');
            input.setAttribute('pattern', '[0-9]*');
        });
        
        // 为邮箱输入添加邮箱键盘
        document.querySelectorAll('input[type="email"]').forEach(input => {
            input.setAttribute('inputmode', 'email');
        });
        
        // 为 URL 输入添加 URL 键盘
        document.querySelectorAll('input[type="url"]').forEach(input => {
            input.setAttribute('inputmode', 'url');
        });
    }
    
    /**
     * 设置缩放控制
     */
    setupZoomControl() {
        // 禁用双击缩放（在某些情况下）
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    /**
     * 设置移动端导航
     */
    setupMobileNavigation() {
        // 创建移动端导航栏
        this.createMobileNav();
        
        // 创建移动端菜单
        this.createMobileMenu();
    }
    
    /**
     * 创建移动端导航栏
     */
    createMobileNav() {
        const nav = document.createElement('div');
        nav.className = 'mobile-nav';
        nav.innerHTML = `
            <div class="mobile-nav-title">TTS 服务</div>
            <button class="mobile-nav-menu" onclick="mobileDetector.toggleMobileMenu()">
                ☰
            </button>
        `;
        
        document.body.insertBefore(nav, document.body.firstChild);
    }
    
    /**
     * 创建移动端菜单
     */
    createMobileMenu() {
        const menu = document.createElement('div');
        menu.className = 'mobile-menu';
        menu.id = 'mobile-menu';
        
        // 获取当前页面的导航链接
        const menuItems = this.getMobileMenuItems();
        
        menu.innerHTML = menuItems.map(item => 
            `<a href="${item.href}" class="mobile-menu-item">${item.icon} ${item.text}</a>`
        ).join('');
        
        document.body.insertBefore(menu, document.body.children[1]);
        
        // 点击菜单项后关闭菜单
        menu.addEventListener('click', (e) => {
            if (e.target.classList.contains('mobile-menu-item')) {
                this.closeMobileMenu();
            }
        });
        
        // 点击页面其他地方关闭菜单
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.mobile-nav') && !e.target.closest('.mobile-menu')) {
                this.closeMobileMenu();
            }
        });
    }
    
    /**
     * 获取移动端菜单项
     */
    getMobileMenuItems() {
        const currentPath = window.location.pathname;
        
        const allItems = [
            { href: '/', icon: '🏠', text: '首页' },
            { href: '/tts', icon: '🎙️', text: 'TTS 转换' },
            { href: '/admin', icon: '⚙️', text: '管理面板' },
            { href: '/api/status', icon: '📊', text: '服务状态' },
            { href: '/health', icon: '💚', text: '健康检查' }
        ];
        
        // 根据当前页面过滤菜单项
        return allItems.filter(item => item.href !== currentPath);
    }
    
    /**
     * 切换移动端菜单
     */
    toggleMobileMenu() {
        const menu = document.getElementById('mobile-menu');
        if (menu) {
            menu.classList.toggle('open');
        }
    }
    
    /**
     * 关闭移动端菜单
     */
    closeMobileMenu() {
        const menu = document.getElementById('mobile-menu');
        if (menu) {
            menu.classList.remove('open');
        }
    }
    
    /**
     * 设置屏幕方向监听
     */
    setupOrientationListener() {
        const handleOrientationChange = () => {
            setTimeout(() => {
                const newOrientation = this.getOrientation();
                document.body.classList.remove('portrait', 'landscape');
                document.body.classList.add(newOrientation);
                
                // 触发自定义事件
                const orientationEvent = new CustomEvent('orientationchange', {
                    detail: { orientation: newOrientation }
                });
                document.dispatchEvent(orientationEvent);
                
                console.log('屏幕方向变化:', newOrientation);
            }, 100);
        };
        
        // 监听方向变化
        if (screen.orientation) {
            screen.orientation.addEventListener('change', handleOrientationChange);
        } else {
            window.addEventListener('orientationchange', handleOrientationChange);
        }
        
        // 初始设置
        handleOrientationChange();
    }
    
    /**
     * 设置窗口大小变化监听 - 基于屏幕宽度重新检测
     */
    setupResizeListener() {
        let resizeTimer;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                // 保存之前的状态
                const wasMobile = this.isMobile;
                const wasTablet = this.isTablet;
                const wasDeviceType = this.deviceType;
                
                // 重新检测设备类型（基于新的屏幕宽度）
                this.isMobile = this.detectMobile();
                this.isTablet = this.detectTablet();
                this.deviceType = this.getDeviceType();
                
                // 检查是否有变化
                const deviceChanged = wasMobile !== this.isMobile || 
                                    wasTablet !== this.isTablet || 
                                    wasDeviceType !== this.deviceType;
                
                if (deviceChanged) {
                    console.log(`设备类型变化: ${wasDeviceType} -> ${this.deviceType} (宽度: ${window.innerWidth}px)`);
                    this.reinitialize();
                }
                
                // 触发自定义事件
                const resizeEvent = new CustomEvent('deviceresize', {
                    detail: {
                        ...this.getDeviceInfo(),
                        changed: deviceChanged,
                        previousType: wasDeviceType
                    }
                });
                document.dispatchEvent(resizeEvent);
                
                // 输出调试信息
                console.log('屏幕尺寸变化:', {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    deviceType: this.deviceType,
                    changed: deviceChanged
                });
            }, 250);
        });
    }
    
    /**
     * 重新初始化 - 基于新的屏幕宽度
     */
    reinitialize() {
        // 移除旧的设备类型类名
        document.body.classList.remove('device-mobile', 'device-tablet', 'device-desktop');
        
        // 添加新的设备类型类名
        document.body.classList.add(`device-${this.deviceType}`);
        
        // 更新触摸设备类名
        if (this.touchSupport) {
            document.body.classList.add('touch-device');
        } else {
            document.body.classList.remove('touch-device');
        }
        
        // 重新设置视口
        this.setupViewport();
        
        // 更新移动端样式
        const existingStyles = document.getElementById('mobile-styles');
        if (this.isMobile || this.isTablet) {
            if (existingStyles) {
                existingStyles.textContent = this.getMobileCSS();
            } else {
                this.loadMobileStyles();
            }
            
            // 确保移动端导航存在
            if (!document.querySelector('.mobile-nav')) {
                this.setupMobileNavigation();
            }
        } else {
            // 桌面端时移除移动端样式
            if (existingStyles) {
                existingStyles.remove();
            }
            
            // 移除移动端导航
            const mobileNav = document.querySelector('.mobile-nav');
            const mobileMenu = document.querySelector('.mobile-menu');
            if (mobileNav) mobileNav.remove();
            if (mobileMenu) mobileMenu.remove();
        }
        
        console.log(`设备重新初始化完成: ${this.deviceType} (${window.innerWidth}x${window.innerHeight})`);
    }
    
    /**
     * 获取性能信息
     */
    getPerformanceInfo() {
        return {
            deviceMemory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            } : 'unknown'
        };
    }
    
    /**
     * 启用调试模式
     */
    enableDebugMode() {
        // 添加调试信息显示
        const debugInfo = document.createElement('div');
        debugInfo.id = 'mobile-debug-info';
        debugInfo.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 10000;
            max-width: 200px;
        `;
        
        const updateDebugInfo = () => {
            const info = this.getDeviceInfo();
            const performance = this.getPerformanceInfo();
            
            debugInfo.innerHTML = `
                <strong>设备信息</strong><br>
                类型: ${info.deviceType}<br>
                触摸: ${info.touchSupport ? '是' : '否'}<br>
                屏幕: ${info.screenWidth}x${info.screenHeight}<br>
                方向: ${info.orientation}<br>
                内存: ${performance.deviceMemory}GB<br>
                CPU: ${performance.hardwareConcurrency}核<br>
                网络: ${performance.connection.effectiveType || 'unknown'}
            `;
        };
        
        updateDebugInfo();
        document.body.appendChild(debugInfo);
        
        // 定期更新调试信息
        setInterval(updateDebugInfo, 1000);
        
        // 双击隐藏/显示
        debugInfo.addEventListener('dblclick', () => {
            debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
        });
    }
}

// 创建全局实例
const mobileDetector = new MobileDetector();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileDetector;
}