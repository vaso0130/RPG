class World:
    def __init__(self):
        self.locations = {}
        self.time = 0
        self.races = {
            "人類": {"description": "適應力強，在世界各地都能找到他們的蹤跡。", "skills": []},
            "城市精靈": {"description": "優雅而敏捷，擅長在都市叢林中穿梭。", "skills": ["都市潛行"]},
            "木精靈": {"description": "與自然和諧共生，是森林的守護者。", "skills": ["自然感應"]},
            "沙漠精靈": {"description": "堅韌不拔，能在嚴酷的沙漠環境中生存。", "skills": ["沙塵暴"]},
            "黑暗精靈": {"description": "居住在地底深處，擅長使用黑暗魔法。", "skills": ["暗影術"]},
            "矮人": {"description": "強壯而堅毅的工匠，擅長打造武器和盔甲。", "skills": ["精工製作"]},
            "半獸人（森林）": {"description": "擁有野性的力量，是森林中的優秀獵人。", "skills": ["野性衝鋒"]},
            "半獸人（海洋）": {"description": "適應海洋生活，能在水中自由呼吸。", "skills": ["水下呼吸"]},
            "龍裔": {"description": "擁有龍的血脈，天生就具有強大的力量。", "skills": ["龍之吐息"]},
        }
        self.items = {
            # 消耗品
            "治療藥水": {
                "type": "消耗品",
                "description": "一瓶能迅速癒合傷口的紅色藥水。",
                "effect": {"heal": 20}
            },
            "煙霧彈": {
                "type": "消耗品",
                "description": "製造濃煙，方便脫身或偷襲。",
                "effect": {"action": "escape"} 
            },
            "解毒劑": {
                "type": "消耗品",
                "description": "能中和多種常見毒素的血清。",
                "effect": {"cure": "poison"} 
            },
            "戰鬥興奮劑": {
                "type": "消耗品",
                "description": "短時間內大幅提升身體能力的藥劑，但有副作用。",
                "effect": {"buff": {"STR": 2, "DEX": 2, "duration": 3}}
            },

            # 一般裝備
            "舊警用手槍": {
                "type": "一般裝備",
                "slot": "weapon",
                "description": "一把可靠但略顯老舊的警用手槍。",
                "bonus": {"DEX": 1}
            },
            "鎮暴裝甲": {
                "type": "一般裝備",
                "slot": "torso",
                "description": "由強化塑膠板製成的盔甲，能有效抵禦鈍擊。",
                "bonus": {"CON": 1}
            },
            "登山靴": {
                "type": "一般裝備",
                "slot": "feet",
                "description": "抓地力很強的靴子，適合在崎嶇地形中行走。",
                "bonus": {} # 特定情境加成，暫不設定
            },
            "夜視鏡": {
                "type": "一般裝備",
                "slot": "head",
                "description": "在低光源環境下提供清晰的視野。",
                "ability": "夜視"
            },

            # 特製裝備
            "電漿護腕": {
                "type": "特製裝備",
                "slot": "arms",
                "description": "一個高科技護腕，能投射出小型能量盾。",
                "bonus": {"CON": 2},
                "ability": "能量盾"
            },
            "駭客義體": {
                "type": "特製裝備",
                "slot": "accessory",
                "description": "植入神經系統的微型電腦，能直接與電子設備接口。",
                "bonus": {"INT": 2},
                "ability": "駭入"
            },
            "光學迷彩夾克": {
                "type": "特製裝備",
                "slot": "torso",
                "description": "能扭曲光線，讓穿戴者融入環境。",
                "bonus": {"DEX": 1},
                "ability": "光學迷彩"
            },

            # 神器
            "月神護符": {
                "type": "神器",
                "slot": "accessory",
                "description": "一枚古老的銀製護符，在月光下會發出微光。",
                "faith_effect": {"月神": 5},
                "ability": "月光祝福"
            },
            "太陽神徽記": {
                "type": "神器",
                "slot": "accessory",
                "description": "黃金打造的太陽徽記，觸摸時能感受到溫暖。",
                "faith_effect": {"太陽神": 5},
                "ability": "烈日之光"
            },
            "星辰披風": {
                "type": "神器",
                "slot": "torso",
                "description": "午夜藍的布料上繡著緩慢移動的星辰，穿上它彷彿能洞悉命運的軌跡。",
                "bonus": {"WIS": 3},
                "ability": "星之指引"
            },
            "巨人之力腰帶": {
                "type": "神器",
                "slot": "accessory",
                "description": "由遠古巨人的皮革製成，扣環是一塊未經雕琢的黑曜石，能賜予穿戴者無窮的力量。",
                "bonus": {"STR": 3},
                "ability": "巨人蠻力"
            },
            "旅者之靴": {
                "type": "神器",
                "slot": "feet",
                "description": "一雙看起來飽經風霜的舊靴子，但穿上它之後，任何崎嶇的地形都如履平地。",
                "bonus": {"DEX": 2},
                "ability": "大地漫遊"
            },

            # 魔王遺物
            "低語匕首": {
                "type": "魔王遺物",
                "slot": "weapon",
                "description": "一把由黑曜石打造的匕首，似乎會在你耳邊低語。",
                "corruption_effect": 5,
                "bonus": {"STR": 2},
                "curse": "持有者會時常聽到幻聽，進行專注相關的檢定時可能會有減益。"
            },
            "腐化之顱": {
                "type": "魔王遺物",
                "slot": "accessory", 
                "description": "一個不知名生物的頭骨，上面刻滿了扭曲的符文，散發著不祥的氣息。",
                "corruption_effect": 10,
                "bonus": {"INT": 1, "WIS": 1},
                "curse": "你的夢境將會被噩夢侵擾，可能導致減益或觸發特殊事件。"
            },
            "噬魂之刃": {
                "type": "魔王遺物",
                "slot": "weapon",
                "description": "劍刃上流動著被吞噬靈魂的痛苦哀嚎，每一次揮砍都渴望著新的祭品。",
                "corruption_effect": 8,
                "bonus": {"STR": 3},
                "curse": "殺戮的慾望會逐漸侵蝕你的心智，在未見血時可能導致屬性減益。"
            },
            "混沌法球": {
                "type": "魔王遺物",
                "slot": "accessory",
                "description": "一顆內部有著混亂風暴的水晶球，凝視它的人會看到瘋狂的可能性。",
                "corruption_effect": 7,
                "bonus": {"INT": 3},
                "curse": "你的法術可能會產生意想不到的災難性後果（Wild Magic Surge）。"
            },
            "謊言面具": {
                "type": "魔王遺物",
                "slot": "head",
                "description": "一張看似平靜的白色面具，戴上它的人可以說出最令人信服的謊言，但面具下的臉將逐漸被他人遺忘。",
                "corruption_effect": 6,
                "bonus": {"CHA": 3},
                "curse": "你最親近的人將會慢慢無法辨認出你，影響社交互動。"
            }
        }

    def add_item_definition(self, item_name, item_definition):
        """Dynamically adds a new item definition to the world."""
        if item_name in self.items:
            print(f"【系統警告】試圖覆蓋現有的物品定義：{item_name}")
            return
        self.items[item_name] = item_definition
        print(f"【系統】新的物品知識已加入世界：{item_name}")
