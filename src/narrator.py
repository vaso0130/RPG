import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re

load_dotenv()

# --- Constants ---
# 將重複的 Prompt 指令抽出來，方便維護
_NARRATIVE_PROMPT_TEMPLATE = """
作為這個RPG世界的遊戲管理員(GM)，請根據玩家的行動和結果，生動地描述接下來發生的事情。
玩家資訊：{player_info}
玩家行動：'{action}'
擲骰結果：{outcome_str}

你的核心任務是推動故事發展，並根據情境給予獎勵或後果。
**請務必參考玩家的「特殊能力」和「詛咒」，將它們的效果融入到敘述中。**
你可以選擇給予玩家一個已知的物品，或是在極其稀有、關鍵的時刻，創造一個全新的傳說物品（神器或魔王遺物）。

請嚴格按照以下格式回傳，不要有任何多餘的文字，若無變化則該行省略：

成長點數:[數字]
信仰:[神祇名稱],[+/-點數]
腐化:[+/-點數]
獲得物品:[物品名稱]
創建物品:
{{
    "type": "[類型: 一般裝備/特製裝備/神器/魔王遺物]",
    "slot": "[裝備位置: weapon/head/torso/arms/legs/feet/accessory]",
    "description": "[物品的詳細描述]",
    "bonus": {{ "屬性": 點數 }},
    "faith_effect": {{ "神祇": 點數 }},
    "corruption_effect": 點數,
    "ability": "[物品帶有的主動或被動能力]",
    "curse": "[物品的詛咒效果]"
}}
敘述:[接下來發生的事情]

--- 重要規則 ---
1.  **創造時機**: 創造新物品應該是非常罕見的事件，只在劇情達到高潮或玩家有重大發現時發生。
2.  **格式準確**: 「創建物品」區塊必須是完整的 JSON 格式。如果新物品沒有某個屬性（例如沒有詛咒），請直接省略該鍵值對，不要留空值。
3.  **名稱對應**: 只有在「創建物品」區塊被填寫時，「獲得物品」的名稱才應該是這個新創造的物品。否則，「獲得物品」應從已知物品列表選取。
4.  **敘述為本**: 「敘述」是必要部分，必須提供。

--- 範例 (創造神器) ---
獲得物品:淚光之石
創建物品:
{{
    "type": "神器",
    "slot": "accessory",
    "description": "一顆在月光下會散發出柔和微光的石頭，傳說是由月神的眼淚凝結而成。觸摸它時能感受到一股寧靜祥和的力量。",
    "bonus": {{
        "WIS": 1
    }},
    "faith_effect": {{
        "月神": 3
    }},
    "ability": "心靈平靜"
}}
敘述:當你觸碰祭壇中央的凹槽時，你手中的普通石頭突然發出耀眼的光芒！光芒散去後，一顆美麗的寶石靜靜地躺在你的掌心，它的能量讓你感到前所未有的平靜。
"""

class Narrator:
    def __init__(self):
        """
        初始化敘事者，設置 Gemini API。
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("未找到 GEMINI_API_KEY 環境變數")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])

    def describe_scene(self, player, world):
        """
        使用 Gemini API 生成場景描述。
        """
        prompt = f"玩家 {player.name} ({player.race}) 的屬性為 {player.attributes}，現在位於 {player.location}。請描述一下周圍的環境和發生的事情。"
        response = self.chat.send_message(prompt)
        return response.text

    def generate_location_description(self, location_name):
        """
        使用 Gemini API 生成地點描述。
        """
        prompt = f"""請為這個RPG遊戲生成一個地點的詳細描述。
地點名稱：{location_name}
世界觀：這是一個有科技、魔法與超能力、神話生物存在的現代平行地球。現在地球上的大都市小城市，都會在這世界出現。
請根據這個世界觀，為 {location_name} 產生一段生動的描述，包含它的特色、氛圍和可能的遭遇。"""
        response = self.chat.send_message(prompt)
        return response.text

    def evaluate_action(self, action, player, world):
        """
        使用 Gemini API 評估玩家的動作，決定是否合理、是否需要擲骰，以及擲骰的參數。
        """
        player_total_attrs = player.get_total_attributes(world)
        player_abilities = player.get_active_abilities(world)
        player_curses = player.get_curses(world)

        prompt = f"""這是一個RPG遊戲的GM請求。
玩家：{player.name} ({player.race})
屬性：{player_total_attrs}
地點：{player.location}
特殊能力: {player_abilities if player_abilities else '無'}
詛咒: {player_curses if player_curses else '無'}
玩家動作：'{action}'

請根據玩家的屬性、能力、詛咒、動作和情境判斷：
1.  這個動作在當前情境下是否合理？
2.  這個動作是否需要透過擲骰來決定成功與否？（例如：攻擊、說服、潛行等需要判斷，而簡單的移動或對話則不需要）
3.  如果需要擲骰，需要擲幾顆d20？（根據難度決定，1-5顆）
4.  如果需要擲骰，成功的目標值是多少？（根據難度決定，1-100）

請嚴格按照以下格式回傳，不要有任何多餘的文字：
合理性(是/否),需要擲骰(是/否),擲骰顆數(數字),目標值(數字),原因/說明

範例：
是,是,2,30,因為你想說服守衛，這有一定難度。
是,否,0,0,你只是想走進酒吧，這不需要擲骰。
否,否,0,0,你不能在城市中心召喚隕石雨。
是,是,1,15,你擁有「光學迷彩」能力，潛行難度降低了。
"""
        response = self.chat.send_message(prompt)
        try:
            parts = response.text.strip().split(',')
            is_valid = parts[0] == '是'
            needs_roll = parts[1] == '是'
            num_dice = int(parts[2])
            target = int(parts[3])
            reason = parts[4]
            return is_valid, reason, needs_roll, num_dice, target
        except Exception as e:
            print(f"【錯誤】解析AI回應時發生錯誤：{e}\n原始回應：{response.text}")
            return False, "GM似乎有點困惑，請換個方式說說你的想法。", False, 0, 0

    def get_no_roll_outcome(self, action, player, world):
        """
        對於不需要擲骰的動作，直接生成結果。
        """
        player_info = (
            f"{player.name} ({player.race}, HP: {player.hp}/{player.get_max_hp(world)}, "
            f"屬性: {player.get_total_attributes(world)}, "
            f"腐化: {player.corruption}, 信仰: {player.faith}, "
            f"特殊能力: {player.get_active_abilities(world) if player.get_active_abilities(world) else '無'}, "
            f"詛咒: {player.get_curses(world) if player.get_curses(world) else '無'})"
        )
        prompt = _NARRATIVE_PROMPT_TEMPLATE.format(
            player_info=player_info,
            action=action,
            outcome_str="無 (非判定動作)"
        )
        response = self.chat.send_message(prompt)
        return self._parse_narrative_response(response.text)

    def narrate_outcome(self, action, dice_roll, is_success, player, world):
        """
        使用 Gemini API 根據擲骰結果和動作決定結果。
        """
        success_str = "成功" if is_success else "失敗"
        outcome_str = f"擲骰 {dice_roll} -> {success_str}"
        player_info = (
            f"{player.name} ({player.race}, HP: {player.hp}/{player.get_max_hp(world)}, "
            f"屬性: {player.get_total_attributes(world)}, "
            f"腐化: {player.corruption}, 信仰: {player.faith}, "
            f"特殊能力: {player.get_active_abilities(world) if player.get_active_abilities(world) else '無'}, "
            f"詛咒: {player.get_curses(world) if player.get_curses(world) else '無'})"
        )
        
        prompt = _NARRATIVE_PROMPT_TEMPLATE.format(
            player_info=player_info,
            action=action,
            outcome_str=outcome_str
        )
        response = self.chat.send_message(prompt)
        return self._parse_narrative_response(response.text)

    def _parse_narrative_response(self, response_text):
        """
        解析來自 AI 的複雜敘述回應，現在能處理動態生成的物品。
        """
        try:
            gp_awarded = 0
            faith_change = None
            corruption_change = 0
            item_received = None
            new_item_definition = None
            narrative = ""

            # 1. 優先解析並提取「創建物品」的 JSON 區塊
            item_def_match = re.search(r"創建物品:\s*(\{.*?\})", response_text, re.DOTALL)
            if item_def_match:
                json_str = item_def_match.group(1)
                try:
                    new_item_definition = json.loads(json_str)
                    # 從原始文本中移除已解析的區塊，避免干擾後續解析
                    response_text = response_text.replace(item_def_match.group(0), "")
                except json.JSONDecodeError as e:
                    print(f"【錯誤】解析AI創造的物品JSON時發生錯誤：{e}\n原始JSON字串：{json_str}")

            # 2. 逐行解析剩餘的內容
            lines = response_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("成長點數:"):
                    gp_awarded = int(line.split(':')[1].strip())
                elif line.startswith("信仰:"):
                    parts = line.split(':')[1].strip().split(',')
                    faith_change = (parts[0].strip(), int(parts[1].strip()))
                elif line.startswith("腐化:"):
                    corruption_change = int(line.split(':')[1].strip())
                elif line.startswith("獲得物品:"):
                    item_received = line.split(':')[1].strip()
                elif line.startswith("敘述:"):
                    narrative = line.split(':', 1)[1].strip()
                elif "敘述:" not in response_text: # 如果完全沒有敘述標籤，將無法被解析的行視為敘述的一部分
                    narrative += line + "\n"

            # 如果解析後敘述為空，但原始文本中有內容，則將整個剩餘文本視為敘述
            if not narrative.strip() and response_text.strip():
                 # 清理掉可能殘留的標籤
                clean_text = re.sub(r"^(成長點數|信仰|腐化|獲得物品):.*?\n?", "", response_text, flags=re.MULTILINE).strip()
                narrative = clean_text

            return narrative, gp_awarded, faith_change, corruption_change, item_received, new_item_definition

        except Exception as e:
            print(f"【錯誤】解析AI敘述時發生錯誤：{e}\n原始回應：{response_text}")
            return response_text, 0, None, 0, None, None

    def generate_improvised_character(self, player, world):
        """
        使用 Gemini API 生成一個即興的角色與開場。
        """
        print("\n【系統】正在為你生成即興冒險，請稍候...")
        races_list = list(world.races.keys())
        prompt = f"""這是一個RPG遊戲的即興角色生成請求。
請根據以下世界觀和規則，隨機生成一位角色和他的開場冒險：

世界觀：科技、魔法與神話融合的現代平行地球。
可選種族：{', '.join(races_list)}

生成規則：
1.  隨機選擇一個種族。
2.  為角色取一個適合的名字。
3.  撰寫一段簡短但有趣的角色背景故事（職業、經歷等）。
4.  將總共 10 點的屬性點數隨機分配到 STR, DEX, CON, INT, WIS, CHA 上（基礎值為10）。
5.  設計一個獨特的開場情境，並指定一個初始地點。

請嚴格按照以下格式回傳，不要有任何多餘的文字，每項佔一行：
姓名: [角色姓名]
種族: [選擇的種族]
背景: [角色背景故事]
力量: [數字]
敏捷: [數字]
體質: [數字]
智力: [數字]
感知: [數字]
魅力: [數字]
初始地點: [地點名稱]
開場描述: [遊戲的開場第一段敘述]
"""
        try:
            response = self.chat.send_message(prompt)
            lines = response.text.strip().split('\n')
            char_data = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(':', 1)
                    char_data[key.strip()] = value.strip()

            player.name = char_data.get("姓名", "無名者")
            player.race = char_data.get("種族", "人類")
            player.background = char_data.get("背景", "一個謎團")
            player.attributes["STR"] = int(char_data.get("力量", 10))
            player.attributes["DEX"] = int(char_data.get("敏捷", 10))
            player.attributes["CON"] = int(char_data.get("體質", 10))
            player.attributes["INT"] = int(char_data.get("智力", 10))
            player.attributes["WIS"] = int(char_data.get("感知", 10))
            player.attributes["CHA"] = int(char_data.get("魅力", 10))
            player.location = char_data.get("初始地點", "未知的街道")
            opening_line = char_data.get("開場描述", "你在一陣暈眩中醒來，不知身在何處。")

            # 根據種族設定初始技能
            if player.race in world.races:
                player.skills = world.races[player.race].get('skills', [])

            print("\n--- 角色生成完畢 ---")
            print(f"姓名: {player.name}")
            print(f"種族: {player.race}")
            print(f"背景: {player.background}")
            print("屬性:")
            for attr, value in player.attributes.items():
                print(f"  {attr}: {value}")
            print(f"初始技能: {', '.join(player.skills) if player.skills else '無'}")
            print("-" * 20)
            print("\n" + opening_line)

        except Exception as e:
            print(f"【錯誤】生成即興角色時發生錯誤：{e}。將使用預設角色開始。")
            player.name = "旅人"
            player.race = "人類"
            player.location = "邊境小鎮"
            print("你是一位來自遠方的旅人，剛抵達一個名為『起點』的邊境小鎮。")
