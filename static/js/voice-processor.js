/**
 * 声音数据预处理器
 * 负责将原始声音数据转换为支持旁白/对话分类的格式
 */
class VoiceDataProcessor {
    constructor() {
        this.processedVoices = {};
    }

    /**
     * 处理声音数据，将原始数据转换为分类格式
     * @param {Object} rawVoices - 原始声音数据
     * @returns {Object} 处理后的分类声音数据
     */
    processVoiceData(rawVoices) {
        const processedData = {};
        
        for (const [language, voiceList] of Object.entries(rawVoices)) {
            processedData[language] = {
                all: voiceList.filter(voice => voice !== "No"),
                narration: [],
                dialogue: []
            };

            // 对每个声音进行分类
            voiceList.forEach(voice => {
                if (voice === "No") return;
                
                const category = this.categorizeVoice(voice);
                if (category.includes('narration')) {
                    processedData[language].narration.push(voice);
                }
                if (category.includes('dialogue')) {
                    processedData[language].dialogue.push(voice);
                }
            });
        }

        this.processedVoices = processedData;
        return processedData;
    }

    /**
     * 根据声音特征进行分类
     * @param {string} voiceName - 声音名称
     * @returns {Array} 分类数组，可能包含 'narration', 'dialogue'
     */
    categorizeVoice(voiceName) {
        const categories = [];
        
        // 基于声音名称的分类规则
        const narrationKeywords = [
            'Yunjian', 'Yunxi', 'Conrad', 'Henri', 'Brian', 'Guy', 'Davis', 'Tony',
            'Hamed', 'Shakir', 'Bassel', 'Taim', 'Fahed', 'Rami', 'Omar', 'Jamal',
            'Abdullah', 'Moaz', 'Laith', 'Hedi', 'Hamdan', 'Saleh', 'Babek',
            'Pradeep', 'Bashkar', 'Goran', 'Borislav', 'Thiha', 'Enric',
            'WanLung', 'Yunyang', 'Yunxia', 'YunJhe', 'Duarte', 'Dmitry',
            'Mattias', 'Niwat', 'Ahmet', 'Ostap', 'NamMinh'
        ];

        const dialogueKeywords = [
            'Xiaoxiao', 'Xiaoyi', 'HiuGaai', 'HiuMaan', 'HsiaoChen', 'HsiaoYu',
            'Xiaobei', 'Xiaoni', 'Ava', 'Emma', 'Jenny', 'Aria', 'Jane', 'Sara',
            'Nancy', 'Ana', 'Ashley', 'Cora', 'Elizabeth', 'Michelle', 'Monica',
            'Fatima', 'Laila', 'Amina', 'Salma', 'Rana', 'Sana', 'Noura',
            'Layla', 'Iman', 'Mouna', 'Aysha', 'Amal', 'Zariyah', 'Amany',
            'Reem', 'Maryam', 'Banu', 'Nabanita', 'Tanishaa', 'Vesna',
            'Kalina', 'Nilar', 'Joana'
        ];

        // 检查是否包含旁白关键词
        if (narrationKeywords.some(keyword => voiceName.includes(keyword))) {
            categories.push('narration');
        }

        // 检查是否包含对话关键词
        if (dialogueKeywords.some(keyword => voiceName.includes(keyword))) {
            categories.push('dialogue');
        }

        // 如果没有匹配到特定分类，则同时适用于旁白和对话
        if (categories.length === 0) {
            categories.push('narration', 'dialogue');
        }

        return categories;
    }

    /**
     * 获取处理后的声音数据
     * @returns {Object} 处理后的声音数据
     */
    getProcessedVoices() {
        return this.processedVoices;
    }

    /**
     * 根据语言和类型获取声音列表
     * @param {string} language - 语言代码
     * @param {string} type - 声音类型 ('all', 'narration', 'dialogue')
     * @returns {Array} 声音列表
     */
    getVoicesByType(language, type = 'all') {
        if (!this.processedVoices[language]) {
            return [];
        }
        return this.processedVoices[language][type] || [];
    }
}