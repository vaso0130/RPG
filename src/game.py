import narrator
import player
import world
import json
import os
import random

SAVE_FILE = "savegame.json"

def save_game(p, w, n):
    """
    儲存遊戲狀態，包含玩家、世界和 AI 對話歷史。
    """
    # 將 Gemini 的對話歷史轉換為可序列化的格式
    serializable_history = []
    for content in n.chat.history:
        serializable_history.append({
            "role": content.role,
            "parts": [part.text for part in content.parts]
        })

    save_data = {
        "player": p.__dict__,
        "world": {
            "locations": w.locations,
            "items": w.items
        },
        "narrator_history": serializable_history
    }
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=4)
    print(f"\n【系統】遊戲已儲存至 {SAVE_FILE}。")

def load_game():
    """
    讀取遊戲狀態，回傳重建後的物件。
    """
    if not os.path.exists(SAVE_FILE):
        return None, None, None

    with open(SAVE_FILE, 'r', encoding='utf-8') as f:
        save_data = json.load(f)

    p = player.Player()
    w = world.World()
    n = narrator.Narrator()

    # 恢復玩家和世界狀態
    p.__dict__.update(save_data['player'])
    w.locations = save_data['world']['locations']
    w.items = save_data['world']['items']

    # 恢復 AI 對話歷史
    n.chat = n.model.start_chat(history=save_data['narrator_history'])

    print(f"\n【系統】已從 {SAVE_FILE} 讀取存檔。歡迎回來，{p.name}！")
    return p, w, n

def start_game():
    """
    開始新遊戲。
    """
    p, w, n = None, None, None

    # 遊戲模式選擇
    print("歡迎來到這個世界！")
    if os.path.exists(SAVE_FILE):
        print("1. 🚀 開始新遊戲")
        print("2. 📂 讀取存檔")
        mode_choice = ""
        while mode_choice not in ['1', '2']:
            mode_choice = input("請輸入你的選擇 (1/2): ")
            if mode_choice == '1':
                p, w, n = new_game_setup()
            elif mode_choice == '2':
                p, w, n = load_game()
    else:
        p, w, n = new_game_setup()

    if not p or not w or not n:
        print("【錯誤】遊戲初始化失敗，無法開始。")
        return

    # 遊戲主循環
    while True:
        # 如果玩家沒有地點，設定一個初始地點 (僅限新遊戲)
        if p.location is None:
            initial_location = "台北車站"
            p.location = initial_location
            print(f"\n【系統】遊戲開始！你的冒險從 {initial_location} 開始。")
            # 敘事者描述場景
            scene_description = n.describe_scene(p, w)
            print(scene_description)
        
        # 獲取玩家輸入
        action = input("\n> ")
        action_parts = action.lower().split()
        command = action_parts[0] if action_parts else ""

        # 檢查特殊指令
        if command in ['存檔', 'save']:
            save_game(p, w, n)
            continue
        elif command in ['離開', 'quit', 'exit']:
            confirm = input("確定要離開遊戲嗎？未儲存的進度將會遺失。(是/否) ").lower()
            if confirm in ['是', 'y', 'yes']:
                print("下次再會！")
                break
            else:
                continue
        elif command in ['成長', 'growth']:
            p.manage_growth(w)
            continue
        elif command in ['狀態', 'status']:
            p.show_status(w)
            continue
        elif command in ['使用', 'use'] and len(action_parts) > 1:
            item_name = " ".join(action_parts[1:])
            p.use_item(item_name, w)
            continue
        elif command in ['裝備', 'equip'] and len(action_parts) > 1:
            item_name = " ".join(action_parts[1:])
            p.equip_item(item_name, w)
            continue
        elif command in ['卸下', 'unequip'] and len(action_parts) > 1:
            slot_name = action_parts[1]
            if slot_name in p.equipment:
                p.unequip_item(slot_name, w)
            else:
                print(f"【系統】無效的裝備位置：{slot_name}。有效的為：{', '.join(p.equipment.keys())}")
            continue

        # 處理玩家動作
        result, gp_awarded, faith_change, corruption_change, item_received, new_item_def, skill_received, new_skill_def, miracle_received, new_miracle_def = handle_action(action, p, w, n)
        print(result)

        # 處理新創建的物品
        if new_item_def and item_received:
            w.add_item_definition(item_received, new_item_def)

        # 處理新創建的技能
        if new_skill_def and skill_received:
            w.add_skill_definition(skill_received, new_skill_def)

        # 處理新創建的奇蹟
        if new_miracle_def and miracle_received:
            w.add_miracle_definition(miracle_received, new_miracle_def)

        # 處理成長點數
        if gp_awarded > 0:
            p.growth_points += gp_awarded
            print(f"\n【系統】你獲得了 {gp_awarded} 點成長點數 (GP)！你現在共有 {p.growth_points} GP。")

        # 處理信仰變化
        if faith_change:
            deity, change = faith_change
            p.faith[deity] = p.faith.get(deity, 0) + change
            if change > 0:
                print(f"【系統】你對 {deity} 的信仰加深了 {change}。")
            else:
                print(f"【系統】你對 {deity} 的信仰動搖了 {-change}。")
            # 自動設定主要信仰
            if not p.deity or p.faith.get(p.deity, 0) < p.faith[deity]:
                p.deity = deity
                print(f"【系統】{deity} 已成為你的主要信仰。")

        # 處理腐化變化
        if corruption_change > 0:
            p.corruption += corruption_change
            print(f"【系統】你的腐化值增加了 {corruption_change}。你現在的腐化值是 {p.corruption}。")

        # 處理獲得物品
        if item_received:
            p.add_item(item_received)

        # 處理獲得技能
        if skill_received:
            if skill_received not in p.skills:
                p.skills.append(skill_received)
                print(f"【系統】你學會了新的技能：{skill_received}！")

        # 處理獲得奇蹟
        if miracle_received:
            if miracle_received not in p.miracles:
                p.miracles.append(miracle_received)
                print(f"【系統】你領悟了新的奇蹟：{miracle_received}！")

        # --- 回合結束階段 ---
        end_of_turn_effects(p, w)

        # 檢查遊戲是否結束
        if is_game_over(p, w):
            print("\n--- 遊戲結束 ---")
            p.show_status(w)
            break

def new_game_setup():
    """
    執行新遊戲的標準設定流程。
    """
    w = world.World()
    n = narrator.Narrator()
    p = player.Player()

    print("\n1. ✏️ 角色創建 (詳細設定你的角色)")
    print("2. 🎲 即興冒險 (由AI為你生成角色並直接開始)")
    
    mode_choice = ""
    while mode_choice not in ['1', '2']:
        mode_choice = input("請輸入你的選擇 (1/2): ")
        if mode_choice == '1':
            p.setup_character(w)
        elif mode_choice == '2':
            n.generate_improvised_character(p, w)
        else:
            print("無效的選擇，請重新輸入。")
    return p, w, n

def handle_action(action, p, w, n):
    """
    處理玩家的動作。
    """
    # 由敘事者判斷動作是否合理，以及是否需要擲骰
    is_valid, reason, needs_roll, num_dice, target = n.evaluate_action(action, p, w)
    if not is_valid:
        return reason, 0, None, 0, None, None, None, None, None, None

    # 如果不需要擲骰，直接獲取結果
    if not needs_roll:
        return n.get_no_roll_outcome(action, p, w)

    # 擲骰子
    dice_roll = roll_dice(num_dice)
    print(f"【系統】你擲出了 {num_dice}d20，結果是：{dice_roll} (目標值: {target}) ")
    
    total_roll = sum(dice_roll)
    is_success = total_roll >= target

    if is_success:
        print("【系統】成功！")
    else:
        print("【系統】失敗！")

    # 由敘事者根據擲骰結果和動作決定結果
    return n.narrate_outcome(action, dice_roll, is_success, p, w)


def roll_dice(num_dice=1, sides=20):
    """
    擲骰子。
    """
    # 根據 AGENTS.md，最多5顆骰子
    num_dice = max(1, min(num_dice, 5))
    return [random.randint(1, sides) for _ in range(num_dice)]

def is_game_over(p, w):
    """
    檢查遊戲是否結束。
    """
    if p.hp <= 0:
        print("\n【系統】你的旅程似乎已經到了終點。")
        return True
    # 未來可以加入更多失敗條件，例如腐化過高、世界毀滅等
    return False

def end_of_turn_effects(p, w):
    """
    處理回合結束時的增益/減益效果。
    """
    effects_to_remove = []
    for attr, effects in p.active_effects.items():
        for item_name, details in effects.items():
            details["duration"] -= 1
            if details["duration"] <= 0:
                effects_to_remove.append((attr, item_name))
    
    for attr, item_name in effects_to_remove:
        del p.active_effects[attr][item_name]
        # 如果某个属性的所有效果都没了，就移除该属性的键
        if not p.active_effects[attr]:
            del p.active_effects[attr]
        print(f"【系統】來自 {item_name} 的效果已結束。")

    # 處理裝備的被動效果
    for slot, item_name in p.equipment.items():
        if not item_name:
            continue
        item = w.items.get(item_name)
        if not item:
            continue
        passive = item.get("passive")
        if not passive:
            continue
        if "heal" in passive:
            p.heal(passive["heal"], w)
        if "corruption" in passive:
            p.corruption += passive["corruption"]
            print(
                f"【系統】{item_name} 的黑暗氣息讓你的腐化值增加 {passive['corruption']}。"
            )
