/**
 * 管理面板语音配置功能
 * 实现语音选择、模式切换和预览功能
 */

// 语音数据
const adminVoiceData = {
    "zh": [
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-YunxiNeural", 
        "zh-CN-YunjianNeural",
        "zh-CN-XiaoyiNeural",
        "zh-CN-YunyangNeural"
    ],
    "en": [
        "en-US-AvaNeural",
        "en-US-AndrewNeural",
        "en-US-EmmaNeural",
        "en-US-BrianNeural",
        "en-US-JennyNeural"
    ],
    "ja": [
        "ja-JP-NanamiNeural",
        "ja-JP-KeitaNeural",
        "ja-JP-AoiNeural"
    ],
    "ko": [
        "ko-KR-SunHiNeural",
        "ko-KR-InJoonNeural"
    ]
};

// 更新管理面板语音选项
function updateAdminVoices() {
    console.log('updateAdminVoices 被调用');
    
    const countrySelect = document.getElementById('adminCountrySelect');
    if (!countrySelect) {
        console.error('找不到 adminCountrySelect 元素');
        return;
    }
    
    const selectedCountry = countrySelect.value;
    console.log('选择的语言:', selectedCountry);
    
    if (!selectedCountry || !adminVoiceData[selectedCountry]) {
        clearAdminVoiceSelections();
        return;
    }

    const singleVoiceMode = document.getElementById('adminSingleVoice')?.checked;
    console.log('单一语音模式:', singleVoiceMode);
    
    if (singleVoiceMode) {
        updateAdminSingleVoiceSelect(selectedCountry);
    } else {
        updateAdminMultiVoiceSelects(selectedCountry);
    }
}

// 切换管理面板语音模式
function toggleAdminVoiceMode() {
    console.log('toggleAdminVoiceMode 被调用');
    
    const singleVoiceMode = document.getElementById('adminSingleVoice')?.checked;
    const singleSection = document.getElementById('adminSingleVoiceSection');
    const multiSection = document.getElementById('adminMultiVoiceSection');
    
    if (!singleSection || !multiSection) {
        console.error('找不到语音配置区域元素');
        return;
    }
    
    if (singleVoiceMode) {
        multiSection.classList.add('d-none');
        singleSection.classList.remove('d-none');
        console.log('切换到单一语音模式');
    } else {
        singleSection.classList.add('d-none');
        multiSection.classList.remove('d-none');
        console.log('切换到分离语音模式');
    }
    
    // 更新语音选项
    updateAdminVoices();
}

// 清空管理面板语音选择
function clearAdminVoiceSelections() {
    console.log('清空语音选择');
    
    const selects = ['adminUnifiedVoice', 'narrationVoice', 'dialogueVoice'];
    selects.forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.innerHTML = '<option value="">请先选择语言</option>';
        }
    });
}

// 更新统一语音选择
function updateAdminSingleVoiceSelect(selectedCountry) {
    console.log('更新统一语音选择:', selectedCountry);
    
    const voiceSelect = document.getElementById('adminUnifiedVoice');
    if (!voiceSelect) {
        console.error('找不到 adminUnifiedVoice 元素');
        return;
    }
    
    const voices = adminVoiceData[selectedCountry];
    
    voiceSelect.innerHTML = '';
    
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '请选择语音';
    voiceSelect.appendChild(defaultOption);

    voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice;
        option.textContent = voice;
        voiceSelect.appendChild(option);
    });
    
    console.log(`添加了 ${voices.length} 个语音选项`);
}

// 更新分离语音选择
function updateAdminMultiVoiceSelects(selectedCountry) {
    console.log('更新分离语音选择:', selectedCountry);
    
    const narrationSelect = document.getElementById('narrationVoice');
    const dialogueSelect = document.getElementById('dialogueVoice');
    
    if (!narrationSelect || !dialogueSelect) {
        console.error('找不到分离语音选择元素');
        return;
    }
    
    const voices = adminVoiceData[selectedCountry];
    
    // 更新旁白语音
    narrationSelect.innerHTML = '';
    const narrationDefault = document.createElement('option');
    narrationDefault.value = '';
    narrationDefault.textContent = '请选择旁白语音';
    narrationSelect.appendChild(narrationDefault);
    
    voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice;
        option.textContent = voice;
        narrationSelect.appendChild(option);
    });
    
    // 更新对话语音
    dialogueSelect.innerHTML = '';
    const dialogueDefault = document.createElement('option');
    dialogueDefault.value = '';
    dialogueDefault.textContent = '请选择对话语音';
    dialogueSelect.appendChild(dialogueDefault);
    
    voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice;
        option.textContent = voice;
        dialogueSelect.appendChild(option);
    });
    
    console.log(`为旁白和对话各添加了 ${voices.length} 个语音选项`);
}

// 预览管理面板语音
async function previewAdminVoice(type) {
    console.log('预览语音:', type);
    
    const previewText = document.getElementById('previewText')?.value || '他说"你好世界"然后离开了';
    let voiceId = '';
    
    if (type === 'unified') {
        voiceId = document.getElementById('adminUnifiedVoice')?.value;
    } else if (type === 'narration') {
        voiceId = document.getElementById('narrationVoice')?.value;
    } else if (type === 'dialogue') {
        voiceId = document.getElementById('dialogueVoice')?.value;
    }
    
    if (!voiceId) {
        console.warn('未选择语音');
        if (window.showAlert) {
            showAlert('请先选择语音', 'warning');
        } else {
            alert('请先选择语音');
        }
        return;
    }
    
    try {
        // 构建预览URL
        const params = new URLSearchParams({
            text: previewText,
            narr: voiceId,
            speed: '1.0'
        });
        
        const previewUrl = `/api?${params.toString()}`;
        console.log('预览URL:', previewUrl);
        
        // 创建音频元素并播放
        const audio = new Audio(previewUrl);
        audio.play().catch(error => {
            console.error('播放预览失败:', error);
            if (window.showAlert) {
                showAlert('预览播放失败', 'danger');
            } else {
                alert('预览播放失败');
            }
        });
        
        const typeText = type === 'unified' ? '统一' : type === 'narration' ? '旁白' : '对话';
        if (window.showAlert) {
            showAlert(`正在预览${typeText}语音`, 'info');
        }
        
    } catch (error) {
        console.error('预览语音失败:', error);
        if (window.showAlert) {
            showAlert('预览语音失败', 'danger');
        } else {
            alert('预览语音失败');
        }
    }
}

// 初始化管理面板语音配置
function initializeAdminVoiceConfig() {
    console.log('初始化管理面板语音配置');
    
    // 检查必要的元素是否存在
    const requiredElements = [
        'adminCountrySelect',
        'adminSingleVoice',
        'adminMultiVoice',
        'adminSingleVoiceSection',
        'adminMultiVoiceSection'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.warn('缺少必要的元素:', missingElements);
        return false;
    }
    
    console.log('所有必要元素都存在，语音配置功能已初始化');
    return true;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('管理面板语音配置脚本加载完成');
    
    // 延迟初始化以确保页面元素都已加载
    setTimeout(() => {
        initializeAdminVoiceConfig();
    }, 500);
});

// 导出函数供全局使用
window.updateAdminVoices = updateAdminVoices;
window.toggleAdminVoiceMode = toggleAdminVoiceMode;
window.previewAdminVoice = previewAdminVoice;