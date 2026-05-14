class QuestionClassifier:
    """
    问题分类器

    根据识别出的实体类型和问题关键词，判断问题类型。
    这里做了增强：
    1. 对部分问题不再严格依赖实体类型，避免“辰砂”被识别成 Mineral 后无法问颜色、文献。
    2. 增加更多中文问法兼容。
    """

    def __init__(self):
        pass

    def classify(self, question, entity_info):
        if not question or not entity_info:
            return "unknown"

        question = question.strip()
        entity_type = entity_info.get("type", "")
        entity_name = entity_info.get("entity", "")

        # 去掉一些常见标点，降低匹配失败概率
        q = question.replace("？", "").replace("?", "").replace("，", "").replace(",", "").strip()

        def has_any(keywords):
            return any(k in q for k in keywords)

        # =========================
        # 1. 壁画类问题
        # =========================
        if entity_type == "Mural":
            if has_any([
                "用了哪些颜料",
                "使用了哪些颜料",
                "采用了哪些颜料",
                "包含哪些颜料",
                "有哪些颜料",
                "颜料有哪些",
                "常见哪些颜料",
                "常用哪些颜料"
            ]):
                return "mural_pigments"

            if has_any([
                "分析方法",
                "检测方法",
                "识别方法",
                "鉴定方法",
                "采用了哪些方法",
                "用了哪些方法",
                "通过哪些方法",
                "分析手段",
                "检测手段"
            ]):
                return "mural_methods"

        # =========================
        # 2. 遗址类问题
        # =========================
        if entity_type == "Site":
            if has_any([
                "常见哪些颜料",
                "常用哪些颜料",
                "有哪些颜料",
                "颜料有哪些",
                "包含哪些颜料",
                "使用了哪些颜料",
                "用了哪些颜料",
                "出现了哪些颜料"
            ]):
                return "site_pigments"

            if has_any([
                "有哪些壁画",
                "包含哪些壁画",
                "有哪些洞窟",
                "有哪些墓室",
                "相关壁画",
                "相关洞窟"
            ]):
                return "site_murals"

        # =========================
        # 3. 颜料/矿物通用问题
        # 这里不要严格依赖 Pigment。
        # 因为有些实体比如“辰砂”可能既是颜料名，也可能被识别成矿物。
        # =========================

        # 查询颜色
        if has_any([
            "是什么颜色",
            "什么颜色",
            "颜色是什么",
            "对应什么颜色",
            "呈什么颜色",
            "是哪种颜色",
            "啥颜色",
            "颜色"
        ]):
            return "pigment_color"

        # 查询来源矿物
        if has_any([
            "来源于什么矿物",
            "来源于哪些矿物",
            "对应什么矿物",
            "对应哪些矿物",
            "由什么矿物",
            "来自什么矿物",
            "是什么矿物",
            "哪些矿物",
            "什么矿物",
            "矿物来源",
            "来源"
        ]):
            return "pigment_mineral"

        # 查询颜料类型
        if has_any([
            "属于什么类型",
            "是什么类型",
            "哪种类型",
            "什么类型",
            "类型"
        ]):
            return "pigment_type"

        # 查询识别方法/检测方法
        if has_any([
            "通过哪些方法识别",
            "通过什么方法识别",
            "识别方法",
            "鉴定方法",
            "怎么识别",
            "如何识别",
            "检测方法",
            "分析方法",
            "测试方法",
            "分析手段",
            "检测手段"
        ]):
            # 如果是壁画，优先走壁画方法；否则走颜料/矿物方法
            if entity_type == "Mural":
                return "mural_methods"
            elif entity_type == "Mineral":
                return "mineral_methods"
            else:
                return "pigment_methods"

        # 查询文献证据
        if has_any([
            "有哪些文献支持",
            "哪些文献支持",
            "有什么文献支持",
            "相关文献",
            "参考文献",
            "文献支持",
            "文献依据",
            "研究依据",
            "研究证据",
            "证据",
            "出处",
            "来源文献",
            "论文",
            "研究"
        ]):
            return "pigment_reference"

        # =========================
        # 4. 矿物类问题
        # =========================
        if entity_type == "Mineral":
            if has_any([
                "有哪些元素",
                "包含哪些元素",
                "含有哪些元素",
                "由哪些元素组成",
                "元素组成",
                "组成元素",
                "化学元素",
                "包含什么元素",
                "含有什么元素"
            ]):
                return "mineral_elements"

            if has_any([
                "对应哪些颜料",
                "有哪些颜料",
                "衍生哪些颜料",
                "可以形成哪些颜料",
                "能形成哪些颜料"
            ]):
                return "mineral_pigments"

        # =========================
        # 5. 元素类问题
        # =========================
        if entity_type == "Element":
            if has_any([
                "相关颜料",
                "哪些颜料",
                "含有该元素",
                "含有这个元素",
                "包含该元素",
                "包含这个元素",
                "有哪些颜料"
            ]):
                return "element_pigments"

            if has_any([
                "相关壁画",
                "哪些壁画",
                "含有该元素的壁画",
                "含有这个元素的壁画",
                "有哪些壁画"
            ]):
                return "element_murals"

        return "unknown"