class QuestionClassifier:
    def classify(self, question, entity_info=None):
        if not entity_info:
            return "unknown"

        entity_type = entity_info["type"]

        # 壁画类
        if entity_type == "Mural":
            if any(k in question for k in ["位于哪里", "在哪里", "地点", "遗址", "位于"]):
                return "mural_site"
            if any(k in question for k in ["使用了哪些颜料", "用了哪些颜料", "颜料有哪些", "使用哪些颜料"]):
                return "mural_pigments"
            if any(k in question for k in ["分析方法", "检测方法", "采用了哪些方法", "用了哪些方法"]):
                return "mural_methods"

        # 颜料类
        if entity_type == "Pigment":
            if any(k in question for k in ["什么颜色", "颜色是什么", "对应什么颜色"]):
                return "pigment_color"
            if any(k in question for k in ["来源于什么矿物", "对应什么矿物", "由什么矿物", "属于什么矿物"]):
                return "pigment_mineral"
            if any(k in question for k in ["属于什么类型", "什么类型"]):
                return "pigment_type"
            if any(k in question for k in ["通过哪些方法识别", "识别方法", "鉴定方法", "怎么识别"]):
                return "pigment_methods"
            if any(k in question for k in ["有哪些文献支持", "相关文献", "文献支持", "参考文献", "证据"]):
                return "pigment_reference"

        # 矿物类
        if entity_type == "Mineral":
            if any(k in question for k in ["有哪些元素", "包含哪些元素", "元素组成"]):
                return "mineral_elements"
            if any(k in question for k in ["对应哪些颜料", "有哪些颜料", "衍生哪些颜料"]):
                return "mineral_pigments"
            if any(k in question for k in ["通过哪些方法识别", "识别方法", "鉴定方法", "怎么识别"]):
                return "mineral_methods"

        # 地点类
        if entity_type == "Site":
            if any(k in question for k in ["常见哪些颜料", "有哪些颜料", "使用哪些颜料"]):
                return "site_pigments"

        # 元素类
        if entity_type == "Element":
            if any(k in question for k in ["出现在哪些壁画", "哪些壁画", "相关壁画"]):
                return "element_murals"

        return "unknown"