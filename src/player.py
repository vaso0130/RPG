import math

class Player:
    def __init__(self):
        self.name = ""
        self.race = ""
        self.background = ""
        self.skills = []
        self.miracles = [] # 新增奇蹟列表
        self.inventory = [] # A list of item names
        self.location = None
        self.attributes = {
            "STR": 10, "DEX": 10, "CON": 10,
            "INT": 10, "WIS": 10, "CHA": 10
        }
        self.hp = 100 # Initial placeholder, will be set properly later
        self.active_effects = {} # For temporary effects like buffs/debuffs

        # Equipment slots
        self.equipment = {
            "weapon": None,
            "head": None,
            "torso": None,
            "arms": None,
            "legs": None,
            "feet": None,
            "accessory": None
        }
        self.attribute_points = 10
        self.growth_points = 0
        self.faith = {}  # e.g., {"舊神Ａ": 10, "新神Ｂ": 5}
        self.corruption = 0
        self.deity = None  # 主要信仰的神祇

    def get_max_hp(self, world):
        """Calculates max HP based on CON."""
        total_con = self.get_total_attributes(world).get("CON", 10)
        return 50 + (total_con * 5)

    def take_damage(self, amount):
        """Reduces player's HP."""
        self.hp -= amount
        print(f"【系統】你受到了 {amount} 點傷害。")
        if self.hp <= 0:
            print("【系統】你的生命值歸零，你失去了意識...")
            self.hp = 0

    def heal(self, amount, world):
        """Heals player's HP."""
        max_hp = self.get_max_hp(world)
        self.hp = min(self.hp + amount, max_hp)
        print(f"【系統】你回復了 {amount} 點生命。")

    def add_item(self, item_name):
        """Adds an item to the player's inventory."""
        self.inventory.append(item_name)
        print(f"【系統】你獲得了物品：{item_name}。")

    def use_item(self, item_name, world):
        """Uses a consumable item from the inventory."""
        if item_name not in self.inventory:
            print("【系統】你的物品欄中沒有這個物品。")
            return

        item_details = world.items.get(item_name)
        if not item_details or item_details.get("type") != "消耗品":
            print("【系統】這個物品無法使用。")
            return

        effect = item_details.get("effect", {})
        used = False
        if "heal" in effect:
            self.heal(effect['heal'], world)
            used = True
        elif "cure" in effect:
            print(f"【系統】你使用了 {item_name}，感覺身體中的毒素被中和了。({effect['cure']} 效果已觸發)")
            used = True
        elif "buff" in effect:
            buff_attrs = effect['buff']
            duration = buff_attrs.pop("duration", 3)
            for attr, value in buff_attrs.items():
                if attr in self.attributes:
                    self.active_effects[attr] = self.active_effects.get(attr, {})
                    self.active_effects[attr][item_name] = {"bonus": value, "duration": duration}
                    print(f"【系統】你使用了 {item_name}，你的 {attr} 暫時提升了 {value} 點！")
            used = True

        if used:
            self.inventory.remove(item_name)
        else:
            print(f"【系統】你使用了 {item_name}，但似乎沒有任何效果。 (效果 {effect} 尚未實作)")

    def equip_item(self, item_name, world):
        """Equips an item from the inventory."""
        if item_name not in self.inventory:
            print("【系統】你的物品欄中沒有這個物品。")
            return

        item_details = world.items.get(item_name)
        if not item_details:
            print("【系統】未知的物品。")
            return

        item_type = item_details.get("type")
        slot = item_details.get("slot")

        if not slot or item_type == "消耗品":
            print(f"【系統】{item_name} 無法裝備。")
            return

        # Unequip the current item in the slot, if any
        if self.equipment.get(slot):
            self.unequip_item(slot, world)

        # Equip the new item
        self.equipment[slot] = item_name
        self.inventory.remove(item_name)
        print(f"【系統】你裝備了 {item_name}。")

        # Apply ongoing effects
        if "faith_effect" in item_details:
            for deity, value in item_details["faith_effect"].items():
                self.faith[deity] = self.faith.get(deity, 0) + value
                print(f"【系統】你對 {deity} 的信仰增加了 {value}。")
        if "corruption_effect" in item_details:
            self.corruption += item_details['corruption_effect']
            print(f"【系統】你的腐化值增加了 {item_details['corruption_effect']}。")

        if "curse" in item_details:
            print(f"【系統警告】裝備 {item_name} 的同時，你感覺到一股惡意... ({item_details['curse']})")
        
        self.hp = self.get_max_hp(world) # Recalculate HP after equipment change


    def unequip_item(self, slot, world):
        """Unequips an item from a given slot."""
        item_name = self.equipment.get(slot)
        if not item_name:
            print(f"【系統】{slot} 位置沒有裝備任何物品。")
            return

        # Move item back to inventory
        self.inventory.append(item_name) # Use append instead of add_item to avoid the message
        self.equipment[slot] = None
        print(f"【系統】你卸下了 {item_name}。")

        # Revert ongoing effects
        item_details = world.items.get(item_name)
        if item_details:
            if "faith_effect" in item_details:
                for deity, value in item_details["faith_effect"].items():
                    self.faith[deity] = self.faith.get(deity, 0) - value
                    print(f"【系統】你對 {deity} 的信仰減少了 {value}。")
            if "corruption_effect" in item_details:
                self.corruption -= item_details["corruption_effect"]
                print(f"【系統】你的腐化值減少了 {item_details['corruption_effect']}。")
            if "curse" in item_details:
                print(f"【系統】卸下 {item_name} 後，那股不祥的感覺消失了。")
        
        self.hp = self.get_max_hp(world) # Recalculate HP after equipment change


    def get_active_abilities(self, world):
        """Gets a list of active abilities from equipped items."""
        abilities = []
        for slot, item_name in self.equipment.items():
            if item_name:
                item_details = world.items.get(item_name)
                if item_details and "ability" in item_details:
                    abilities.append(item_details["ability"])
        return abilities

    def get_curses(self, world):
        """Gets a list of active curses from equipped items."""
        curses = []
        for slot, item_name in self.equipment.items():
            if item_name:
                item_details = world.items.get(item_name)
                if item_details and "curse" in item_details:
                    curses.append(item_details["curse"])
        return curses

    def get_total_attributes(self, world):
        """Calculates total attributes including bonuses from equipment and active effects."""
        total_attrs = self.attributes.copy()
        if world:
            for slot, item_name in self.equipment.items():
                if item_name:
                    item_details = world.items.get(item_name)
                    if item_details and "bonus" in item_details:
                        for attr, bonus in item_details["bonus"].items():
                            if attr in total_attrs:
                                total_attrs[attr] += bonus
        
        for attr, effects in self.active_effects.items():
            for item_name, effect_details in effects.items():
                 total_attrs[attr] += effect_details.get("bonus", 0)

        return total_attrs

    def setup_character(self, world):
        """
        引導玩家創建角色。
        """
        # 設置玩家名稱
        self.name = input("請輸入你的名字：")

        # 顯示可選種族
        print("\n請選擇你的種族：")
        races = list(world.races.keys())
        for i, race_name in enumerate(races):
            print(f"{i + 1}. {race_name} - {world.races[race_name]['description']}")

        # 獲取玩家選擇
        choice = -1
        while choice < 0 or choice >= len(races):
            try:
                choice_input = input(f"請輸入你的選擇 (1-{len(races)}): ")
                choice = int(choice_input) - 1
                if choice < 0 or choice >= len(races):
                    print("無效的選擇，請重新輸入。")
            except ValueError:
                print("無效的輸入，請輸入數字。")

        # 設置玩家種族和技能
        chosen_race = races[choice]
        self.race = chosen_race
        self.skills = world.races[chosen_race]['skills']
        print(f"\n你選擇了 {chosen_race}。你的初始技能是：{', '.join(self.skills) if self.skills else '無'}。")
        print("-" * 20)

        # 屬性分配
        print("\n--- 屬性分配 ---")
        print(f"你的基礎屬性皆為 10。你有 {self.attribute_points} 點可以自由分配。")
        
        while self.attribute_points > 0:
            print("\n目前屬性：")
            attr_str = " | ".join([f"{attr}: {value}" for attr, value in self.attributes.items()])
            print(attr_str)
            print(f"剩餘點數: {self.attribute_points}")

            attr_choice = input("請輸入你想調整的屬性 (STR, DEX, CON, INT, WIS, CHA)，或輸入 '重置' 或 '完成'：").upper()

            if attr_choice == '完成':
                if self.attribute_points > 0:
                    confirm = input(f"你還有 {self.attribute_points} 點未分配，確定要完成嗎？(是/否)").lower()
                    if confirm in ['是', 'yes', 'y']:
                        break
                else:
                    break
            
            if attr_choice == '重置':
                self.attributes = {k: 10 for k in self.attributes}
                self.attribute_points = 10
                print("屬性已重置。")
                continue

            if attr_choice not in self.attributes:
                print("無效的屬性，請重新輸入。")
                continue

            try:
                points_to_add = int(input(f"你要在 {attr_choice} 上變更多少點數？ (可使用正負數) "))
                
                if self.attributes[attr_choice] + points_to_add < 1:
                    print("屬性不能低於1。")
                    continue

                if self.attribute_points - points_to_add < 0:
                    print("你的點數不足。")
                    continue
                
                self.attributes[attr_choice] += points_to_add
                self.attribute_points -= points_to_add

            except ValueError:
                print("無效的輸入，請輸入數字。")

        # 背景設定
        print("\n--- 背景設定 ---")
        print("請簡單描述你的角色背景，例如他的職業、過去的經歷、或一個重要的特質。")
        self.background = input("你的背景故事：")

        print("\n--- 角色創建完成 ---")
        print(f"姓名: {self.name}")
        print(f"種族: {self.race}")
        print(f"背景: {self.background}")
        print("最終屬性:")
        for attr, value in self.attributes.items():
            print(f"  {attr}: {value}")
        print(f"初始技能: {', '.join(self.skills) if self.skills else '無'}")
        self.hp = self.get_max_hp(world)
        print(f"生命值 (HP): {self.hp}/{self.hp}")
        print("-" * 20)

    def show_status(self, world):
        """
        顯示角色的完整狀態。
        """
        print("\n--- 角色狀態 ---")
        print(f"姓名: {self.name}")
        print(f"種族: {self.race}")
        print(f"背景: {self.background}")

        max_hp = self.get_max_hp(world)
        print(f"生命值 (HP): {self.hp}/{max_hp}")

        print("\n--- 屬性 (基礎值 + 裝備/效果加成) ---")
        total_attrs = self.get_total_attributes(world)
        attr_parts = []
        for attr, base_value in self.attributes.items():
            total_value = total_attrs[attr]
            bonus = total_value - base_value
            if bonus > 0:
                attr_parts.append(f"{attr}: {total_value} ({base_value} +{bonus})")
            elif bonus < 0:
                attr_parts.append(f"{attr}: {total_value} ({base_value} {bonus})")
            else:
                attr_parts.append(f"{attr}: {base_value}")
        print(" | ".join(attr_parts))

        if self.active_effects:
            print("\n--- 目前效果 ---")
            for attr, effects in self.active_effects.items():
                for item_name, effect_details in effects.items():
                    bonus = effect_details.get('bonus', 0)
                    duration = effect_details.get('duration', '永久')
                    print(f"  - {item_name}: {attr} +{bonus} (剩餘 {duration} 回合)")


        print("\n--- 核心狀態 ---")
        print(f"成長點數 (GP): {self.growth_points}")
        print(f"腐化值: {self.corruption}")
        if self.deity:
            print(f"主要信仰: {self.deity}")
        if self.faith:
            print("信仰詳情:")
            for deity, value in self.faith.items():
                print(f"  - {deity}: {value}")
        else:
            print("信仰: 無")

        print("\n--- 技能、裝備與物品 ---")
        print(f"技能: {', '.join(self.skills) if self.skills else '無'}")
        print(f"奇蹟: {', '.join(self.miracles) if self.miracles else '無'}")
        
        print("裝備:")
        equipped_items_found = False
        for slot, item_name in self.equipment.items():
            if item_name:
                print(f"  - [{slot.capitalize()}]: {item_name}")
                equipped_items_found = True
        if not equipped_items_found:
            print("  - 無")

        print(f"物品欄: {', '.join(self.inventory) if self.inventory else '空'}")
        print("-" * 20)

    def manage_growth(self, world):
        """
        管理角色的成長，包含屬性提升與技能學習。
        """
        while True:
            print("\n--- 角色成長選單 ---")
            print(f"你目前擁有 {self.growth_points} 成長點數 (GP)。")
            print("1. 提升基礎屬性")
            print("2. 學習或進化技能")
            print("3. 返回遊戲")

            choice = input("請選擇你要做什麼：")

            if choice == '1':
                self.increase_attributes(world)
            elif choice == '2':
                self.manage_skills(world)
            elif choice == '3':
                break
            else:
                print("無效的選擇。")

    def increase_attributes(self, world):
        """
        處理屬性提升的邏輯。
        """
        while True:
            print("\n--- 提升屬性 ---")
            total_attrs = self.get_total_attributes(world)
            attr_parts = []
            for attr, base_value in self.attributes.items():
                total_value = total_attrs[attr]
                bonus = total_value - base_value
                if bonus > 0:
                    attr_parts.append(f"{attr}: {total_value} ({base_value} +{bonus})")
                else:
                    attr_parts.append(f"{attr}: {base_value}")
            print(f"目前屬性: {' | '.join(attr_parts)}")
            print(f"剩餘 GP: {self.growth_points}")
            print("輸入屬性名稱以查看提升成本，或輸入 '返回' 離開。")

            attr_choice = input("請選擇要提升的屬性：").upper()

            if attr_choice == '返回':
                break

            if attr_choice not in self.attributes:
                print("無效的屬性。")
                continue

            current_value = self.attributes[attr_choice]
            cost = math.ceil(current_value / 2)

            print(f"將 {attr_choice} 從 {current_value} 提升到 {current_value + 1} 需要 {cost} GP。")
            if self.growth_points < cost:
                print("你的 GP 不足。")
                continue

            confirm = input("確定要提升嗎？ (是/否): ").lower()
            if confirm in ['是', 'yes', 'y']:
                self.attributes[attr_choice] += 1
                self.growth_points -= cost
                print(f"{attr_choice} 已提升至 {self.attributes[attr_choice]}！")
            else:
                print("已取消提升。")

    def manage_skills(self, world):
        """互動式技能學習與進化流程。"""
        while True:
            print("\n--- 技能管理 ---")
            print(f"你目前擁有 {self.growth_points} GP。")
            print("1. 學習新技能")
            print("2. 進化現有技能")
            print("3. 返回成長選單")
            choice = input("請選擇: ")

            if choice == '1':
                self.learn_new_skill(world)
            elif choice == '2':
                self.evolve_existing_skill(world)
            elif choice == '3':
                break
            else:
                print("無效的選擇。")

    def learn_new_skill(self, world):
        """處理學習新技能的邏輯"""
        while True:
            print("\n--- 學習新技能 ---")
            print(f"你目前擁有 {self.growth_points} GP。")
            
            learnable = {}
            idx = 1
            for skill, info in world.skills.items():
                # 檢查玩家是否已有該技能或其進化版
                has_skill_in_tree = False
                for player_skill in self.skills:
                    # 追溯玩家技能的根技能
                    base_skill = player_skill
                    while True:
                        prev_skill_found = False
                        for key, value in world.skill_tree.items():
                            if value['next'] == base_skill:
                                base_skill = key
                                prev_skill_found = True
                                break
                        if not prev_skill_found:
                            break
                    
                    if base_skill == skill:
                        has_skill_in_tree = True
                        break

                if not has_skill_in_tree:
                    print(f"{idx}. {skill} - {info['description']} (花費 {info['cost']} GP)")
                    learnable[str(idx)] = {"name": skill, "cost": info['cost']}
                    idx += 1
            
            if not learnable:
                print("你已學會所有可用的基礎技能，或已擁有其進化版本。")
                return

            choice = input("選擇要學習的技能編號，或輸入 '返回': ")
            if choice == '返回':
                return
            
            if choice in learnable:
                skill_to_learn = learnable[choice]
                cost = skill_to_learn['cost']
                name = skill_to_learn['name']

                if self.growth_points >= cost:
                    confirm = input(f"確定要花費 {cost} GP 學習 {name} 嗎？ (是/否): ").lower()
                    if confirm in ['是', 'y', 'yes']:
                        self.growth_points -= cost
                        self.skills.append(name)
                        print(f"你已成功學習 {name}！")
                    else:
                        print("已取消學習。")
                else:
                    print("你的 GP 不足。")
            else:
                print("無效的選擇。")

    def evolve_skill(self, skill_name, world):
        """嘗試將指定技能進化，成功時回傳 True。"""
        if skill_name not in self.skills:
            print("你沒有這個技能。")
            return False

        tree = world.skill_tree.get(skill_name)
        if not tree:
            print("此技能無法進化。")
            return False

        cost = tree["cost"]
        next_skill = tree["next"]

        if self.growth_points < cost:
            print("你的 GP 不足。")
            return False

        self.skills[self.skills.index(skill_name)] = next_skill
        self.growth_points -= cost
        print(f"{skill_name} 已進化為 {next_skill}！剩餘 {self.growth_points} GP。")
        return True

    def evolve_existing_skill(self, world):
        """互動式技能進化流程。"""
        while True:
            print("\n--- 技能進化 ---")
            print(f"你目前擁有 {self.growth_points} GP。")
            available = {}
            for idx, skill in enumerate(self.skills, start=1):
                if skill in world.skill_tree:
                    info = world.skill_tree[skill]
                    print(f"{idx}. {skill} -> {info['next']} (花費 {info['cost']} GP)")
                    available[str(idx)] = skill
            if not available:
                print("目前沒有可進化的技能。")
                return

            choice = input("選擇要進化的技能編號，或輸入 '返回': ")
            if choice == '返回':
                return
            if choice not in available:
                print("無效的選擇。")
                continue

            self.evolve_skill(available[choice], world)
