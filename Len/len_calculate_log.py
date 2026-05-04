import numpy as np
import math
import time as tm
from len_cal_function import *
from len_set_stat import *

def len_cal_damage(plot_graph, ring, VI_level, time, print_property, directory):
    start_time = tm.time()
    Boss_Guard = 380
    stats = get_final_stats(directory, print_property, 0)
    ascent_stats = get_final_stats(directory, print_property, 1)
    Condition_ARRAY1, Condition_ARRAY2 = burst_time()
    VI_level_factor = [calc_vi_factor(lvl) for lvl in VI_level[:4]]   
    영격_damage, 영격_ignore, 선참_damage, 선참_ignore, 선참_boss, 망혼강림_damage, 망혼강림_ignore = apply_hyper_skills(stats)
    T_화중군자, T_오라웨폰 = get_special_cooldowns(stats)
    T20, T30, T40, T60, T120, T240, T360 = [T(stats, t) for t in (20, 30, 40, 60, 120, 240, 360)]

    def D(pct, base_ign, add_boss=0, add_ign=0, f_dmg=1.0):
        return calc_D(pct, base_ign, Boss_Guard, stats, Damage2, Boss_Damage2, Critical_Damage2, STR2, Attack_Ratio2, add_boss, add_ign, f_dmg)
    
    def Ascent_D(pct, base_ign, add_boss=0, add_ign=0, f_dmg=1.0):
        return calc_Ascent_D(pct, base_ign, Boss_Guard, ascent_stats, add_boss, add_ign, f_dmg)

    timeline_log = []
    state = log_array()
    skill_order = list(state.keys())
    svr_lag = stats['Server_Lag'] * 1000
    buff_dur = stats['Buff_Duration']
    Reuse_Num = 1 + stats["Ability_Prob"] / 100
    seed = seed_ring(stats)
    Skill_lock = 0

    iteration_time = 10 # ms
    for t in range(0*1000, time*1000,iteration_time):
        test_graph = 0
        keys = ["Damage", "Boss_Damage", "Critical_Damage", "STR_with_MY", 
                "Attack_Ratio", "Ignore_Guard"]
        (Damage2, Boss_Damage2, Critical_Damage2, STR2, Attack_Ratio2, 
         Ignore_Guard2) = [stats[k] for k in keys]
        VMatrix_Ignore_Guard = Ignore_Guard2 + (100 - Ignore_Guard2) * 0.2 # 코강

 #-----------버프류 설정 구간--------------------------------------------------------------------------------------------------------------------          
        Final_Damage, Grandis_Final_Damage = 1, 1
        Condition_ARRAY = Condition_ARRAY1 if (t // T120) % 3 == 0 else Condition_ARRAY2
        
        # 오라웨폰 (상시 변경)
        VMatrix_Ignore_Guard += (100 - VMatrix_Ignore_Guard) * 0.16
        Ignore_Guard2 += (100 - Ignore_Guard2) * 0.16
        Final_Damage = 1.06
            
        # 그여축
        if Condition_ARRAY[1] <= (t % T120) < Condition_ARRAY[1] + 40*1000 + svr_lag:
            Damage2 += 40
            Grandis_Final_Damage = 1.15
    
        if Condition_ARRAY[6] <= (t % T60)  <  Condition_ARRAY[6] + 10*buff_dur*1000 + svr_lag: Damage2 += seed["Soul_con"] # 엔버 링크
        if Condition_ARRAY[8] <= (t % (40*1000)) <  Condition_ARRAY[8] + 20*1000 + svr_lag: Damage2 += 17 # 카인 링크
        if Condition_ARRAY[8] <= (t % (20*1000)) <  Condition_ARRAY[8] + 10*1000 + svr_lag: Damage2 += 18 # 모도 링크
        
        # 특수 코어 (쿨감 X)
        if Condition_ARRAY[9] <= t % (120*1000) < Condition_ARRAY[9] + 10*1000:
            if stats["Boss_Slayer"] == 1:   
                Boss_Damage2 += 50
            if stats["Defense_Smash"] == 1: 
                Ignore_Guard2 = VMatrix_Ignore_Guard = 100
        if stats["Fatal_Strike"] == 1 and Condition_ARRAY[9] <= t % (30*1000) < Condition_ARRAY[9] + 4*1000:
            Boss_Damage2 += 100
        
        # 시드링 
        if ring == 1:
            Damage2 += seed["Continuous_dmg"]
            Attack_Ratio2 += seed["Continuous_att"]
            if Condition_ARRAY[7] <= (t % T120) < Condition_ARRAY[7] + seed["Restraint_time"]*1000:
                Attack_Ratio2 += seed["Restraint_att"]              
#-------------------------------------------------------------------------------------------------------------------------------            
        burst_end_time = Condition_ARRAY[10] + 7170 if Condition_ARRAY[10] > 0 else Condition_ARRAY[9] + 5010
        is_combo_active = (state["열지"]["step"] > 0)
        Skill_lock = 1 if ((t % T120) < burst_end_time) or is_combo_active else 0
        
        # 섬무
        섬무, 섬무_사용 = 0, 0
        elapsed_섬무 = t % T120 - Condition_ARRAY[9]   
        if 0 <= elapsed_섬무 <= 5000 and elapsed_섬무 % 90 == 0:
            섬무 = D(VI_level_factor[2] * 6 * 1050, Ignore_Guard2, 0, 0, Final_Damage*Grandis_Final_Damage)
            state["섬무"]["times_used"] += 1
            state["섬무"]["attacks"] += 6
            섬무_사용 = 1

        # 일격예인
        일격예인, 일격예인_사용 = 0, 0
        if state["일격예인"]["delay"] > 0:
            state["일격예인"]["delay"] -= iteration_time
        if state["일격예인"]["delay"] <= 0 and not is_combo_active and (state["일격예인"]["times_used"] > 0 or t >= Condition_ARRAY[8]):
            state["일격예인"]["delay"] = T30 - iteration_time
            state["일격예인"]["step"], state["일격예인"]["action_delay"], state["일격예인"]["burst_count"] = 20, 540 - iteration_time, 0
        if state["일격예인"]["step"] > 0:
            if state["일격예인"]["action_delay"] >= 0:
                Skill_lock = 1
                state["일격예인"]["action_delay"] -= iteration_time
            if state["일격예인"]["burst_count"] <= 0:
                pct = 2.2 * (246 + 4 * VI_level[8] if VI_level[8] > 0 else 214) * 7
                일격예인 = D(pct, VMatrix_Ignore_Guard, 0, 0, Final_Damage)
                state["일격예인"]["times_used"] += 1
                state["일격예인"]["attacks"] += 7
                일격예인_사용 = 1
                state["일격예인"]["step"] -= 1
                if state["일격예인"]["step"] > 0:
                    state["일격예인"]["burst_count"] = 90 - iteration_time
            else:
                state["일격예인"]["burst_count"] -= iteration_time

        # 선참
        선참, 선참_사용 = 0, 0
        if Skill_lock == 0 and state["선참"]["delay"] <= 0:
            pct = 2.2*(202+3*VI_level[5])*5 if VI_level[5] > 0 else 2.2*170*5
            선참 = D(pct, VMatrix_Ignore_Guard, 선참_damage+선참_boss, 선참_ignore, Final_Damage)
            state["선참"]["delay"] = 149 - iteration_time
            state["선참"]["times_used"] += 1
            state["선참"]["attacks"] += 5
            선참_사용 = 1
        else:
            state["선참"]["delay"] -= iteration_time
        
        # 승화 & 망혼강림 콤보
        승화_active = 1 if Condition_ARRAY[4] <= t % T120 < Condition_ARRAY[4] + 15000 + svr_lag else 0
        if 승화_active == 1:
            if Condition_ARRAY[4] <= t % T120 < Condition_ARRAY[4] + iteration_time:
                state["열지"]["delay"] = state["열지"]["step"] = state["열지"]["action_delay"] = state["열지"]["burst_count"] = 0
        else:
            state["열지"]["burst_count"] = 0
            
        열지, 망탄, 무량겁, 심검 = 0, 0, 0, 0
        열지_사용, 망탄_사용, 무량겁_사용, 심검_사용 = 0, 0, 0, 0
        if state["열지"]["delay"] > 0: state["열지"]["delay"] -= iteration_time
        if state["열지"]["action_delay"] > 0: state["열지"]["action_delay"] -= iteration_time
        if state["열지"]["action_delay"] <= 0:
            can_burst = (state["열지"]["step"] == 0 and 승화_active == 1 and 
                         state["열지"]["burst_count"] < 3 and t % T120 >= Condition_ARRAY[9])
            can_normal = (state["열지"]["step"] == 0 and state["열지"]["delay"] <= 0 and 
                          ((승화_active == 0 and Skill_lock == 0) or 
                           (승화_active == 1 and t % T120 >= Condition_ARRAY[9])))
            
            if can_burst or can_normal:
                state["열지"]["step"] = 1
                if can_burst:
                    state["열지"]["burst_count"] += 1
                else:
                    state["열지"]["delay"] = T20 - iteration_time  
                pct = 2.2*(850+10*VI_level[7])*5 + 2.2*(900+15*VI_level[7])*7 if VI_level[7] > 0 else 2.2*550*5 + 2.2*689*7
                열지 = D(pct, VMatrix_Ignore_Guard, 망혼강림_damage, 망혼강림_ignore, Final_Damage*Grandis_Final_Damage)
                state["열지"]["action_delay"] = (90 if 승화_active == 1 else 510) - iteration_time
                state["열지"]["times_used"] += 2
                state["열지"]["attacks"] += 12
                열지_사용 = 1
                
            elif state["열지"]["step"] == 1:
                state["열지"]["step"] = 2
                pct = 2.2*(1350+30*VI_level[7])*9 if VI_level[7] > 0 else 2.2*1260*9
                망탄 = D(pct, VMatrix_Ignore_Guard, 망혼강림_damage, 망혼강림_ignore, Final_Damage*Grandis_Final_Damage)
                state["열지"]["action_delay"] = (90 if 승화_active == 1 else 510) - iteration_time
                state["망탄"]["times_used"] += 1
                state["망탄"]["attacks"] += 9
                망탄_사용 = 1
                
            elif state["열지"]["step"] == 2:
                state["열지"]["step"] = 3
                pct = 2.2*(400+7*VI_level[7])*7*8 if VI_level[7] > 0 else 2.2*380*7*8
                무량겁 = D(pct, VMatrix_Ignore_Guard, 망혼강림_damage, 망혼강림_ignore, Final_Damage*Grandis_Final_Damage)
                state["열지"]["action_delay"] = (90 if 승화_active == 1 else 630) - iteration_time
                state["무량겁"]["times_used"] += 8
                state["무량겁"]["attacks"] += 56
                무량겁_사용 = 1
                
            elif state["열지"]["step"] == 3:
                state["열지"]["step"] = 0
                pct = (1200*10 + 12*1500*3) * VI_level_factor[3]
                심검 = D(pct, VMatrix_Ignore_Guard, 망혼강림_damage, 망혼강림_ignore, Final_Damage*Grandis_Final_Damage)
                state["열지"]["action_delay"] = (570 if 승화_active == 1 else 510) - iteration_time
                state["심검"]["times_used"] += 13
                state["심검"]["attacks"] += 46
                심검_사용 = 1
                
        # 승천
        승천, 승천_사용 = 0, 0
        elapsed_승천 = t % T360 - Condition_ARRAY[10]
        승천_schedule = {
            570: (750,25,9,12),
            1320: (750,25,19,12),
            3150: (720,25,8,12),
            4320: (720,25,22,12),
            5730: (1050,35,27,15)}
        if elapsed_승천 in 승천_schedule:
            승천_ignore = Ignore_Guard2 + (100 - Ignore_Guard2) * get_승천_bonus(VI_level[4])[1]
            승천_boss = get_승천_bonus(VI_level[4])[0]
            base, scale, attacks, times = 승천_schedule[elapsed_승천]
            pct = (base + scale * VI_level[4]) * attacks * times
            승천 = D(pct, 승천_ignore, 승천_boss, 0, Final_Damage*Grandis_Final_Damage)
            승천_사용 = attacks
        if elapsed_승천 == 6300:
            state["승천"]["times_used"] += 85
            state["승천"]["attacks"] += 1101
            
        # 천강, 진천, 낙화 (예인 망혼 빌드 정리 후 적용)
        천강, 진천, 낙화 = 0, 0, 0
        
        # Styx & Phlegethon 
        lvl10 = VI_level[10]
        Styx = 0
        Phlegethon = 0
        hecate_lock = 0
        if lvl10 > 0:
            elapsed_styx = t % T60 - Condition_ARRAY[6] # 엔버 감응
            if 0 <= elapsed_styx <= 3660:
                styx_bonus = 20 * min(2, lvl10 // 10) 
                attacks = 0
                if elapsed_styx == 0:
                    attacks, pct = 8, (644 + 44 * lvl10)
                elif 780 <= elapsed_styx <= 2940 and elapsed_styx % 720 == 60:
                    attacks, pct = 4, (641 + 44 * lvl10)
                elif 3300 <= elapsed_styx <= 3660 and elapsed_styx % 60 == 0:
                    attacks, pct = 7, (731 + 50 * lvl10)
                if attacks > 0:
                    Styx = D(pct * attacks, Ignore_Guard2, styx_bonus, styx_bonus, Final_Damage)
                    state["Styx"]["times_used"] += 1
                    state["Styx"]["attacks"] += attacks
        if lvl10 == 30:
            elapsed_phleg = t % T120 - Condition_ARRAY[7] # 리레 감응
            if 0 <= elapsed_phleg <= 4020:
                hecate_lock = 1
                attacks = 0
                if elapsed_phleg == 960 or (1900 <= elapsed_phleg <= 2980 and elapsed_phleg % 180 == 100):
                    attacks, pct = 4, 1102
                elif 3480 <= elapsed_phleg <= 4020 and elapsed_phleg % 60 == 0:
                    attacks, pct = 6, 877
                if attacks > 0:
                    Phlegethon = D(pct * attacks, Ignore_Guard2, 40, 40, Final_Damage)
                    state["Phlegethon"]["times_used"] += 1
                    state["Phlegethon"]["attacks"] += attacks
                    
# 추가타 ------------------------------------------------------------------        
        # 망혼강림VI
        망혼강림 = 0
        if VI_level[7] > 0:
            current_tick_uses = 0
            if 열지_사용: current_tick_uses += 2
            if 망탄_사용: current_tick_uses += 1
            if 무량겁_사용: current_tick_uses += 8
            if 심검_사용: current_tick_uses += 13
            if current_tick_uses > 0:
                state["망혼강림"]["delay"] += current_tick_uses
                trigger_count = state["망혼강림"]["delay"] // 8
                if trigger_count > 0:
                    state["망혼강림"]["delay"] %= 8
                    pct = (840 + 18 * VI_level[7])*5*2*trigger_count
                    망혼강림 = D(pct, VMatrix_Ignore_Guard, 0, 0, Final_Damage)
                    state["망혼강림"]["times_used"] += 2 * trigger_count
                    state["망혼강림"]["attacks"] += 10 * trigger_count
                    
        # 무량겁 지속 타격
        무량겁_지속 = 0
        if 무량겁_사용 == 1:
            state["무량겁_지속"]["delay"] = 5000
            state["무량겁_지속"]["count"] = 0
        if state["무량겁_지속"]["delay"] > 0:
            state["무량겁_지속"]["delay"] -= iteration_time
            if state["무량겁_지속"]["delay"] % 500 == 0:
                if VI_level[7] > 0:
                    pct = (355 + 2 * VI_level[7]) * 3
                else:
                    pct = 250 * 3
                무량겁_지속 = D(pct, VMatrix_Ignore_Guard, 망혼강림_damage, 망혼강림_ignore, Final_Damage*Grandis_Final_Damage)
                state["무량겁_지속"]["times_used"] += 1
                state["무량겁_지속"]["attacks"] += 3
                    
        # 영격
        영격 = 0
        trigger_count = 선참_사용 + 섬무_사용 
        if trigger_count > 0:
            pct = 2.2* 4 * (820 + 13 * VI_level[6]) if VI_level[6] > 0 else 2.2* 4 * 753
            expected_pct = pct * 0.35 * trigger_count
            영격 = D(expected_pct, VMatrix_Ignore_Guard, 영격_damage, 영격_ignore, Final_Damage)
            state["영격"]["times_used"] += 0.35 * trigger_count
            state["영격"]["attacks"] += 0.35 * 4 * trigger_count
            
        # 연참
        연참 = 0
        trigger_count = (일격예인_사용 + 선참_사용 + 섬무_사용 + 열지_사용*2 + 망탄_사용 + 무량겁_사용*8 + 심검_사용)
        if trigger_count > 0:
            pct = 2.2 * 2 * (235 + 4 * VI_level[6]) if VI_level[6] > 0 else 2.2 * 2 * 215
            expected_pct = pct * 0.62 * trigger_count
            연참 = D(expected_pct, VMatrix_Ignore_Guard, 0, 0, Final_Damage)
            state["연참"]["times_used"] += 0.62 * trigger_count
            state["연참"]["attacks"] += 0.62 * 2 * trigger_count
            
        # 쇄매
        쇄매 = 0
        trigger_count = (일격예인_사용 + 선참_사용 + 섬무_사용 + 승천_사용 + 열지_사용*2 + 망탄_사용 + 무량겁_사용*8 + 심검_사용)
        if trigger_count > 0:
            pct = 2.8 * 3*5 * (120 + 2 * VI_level[8]) if VI_level[8] > 0 else 2.8 * 3*5 * 120
            expected_pct = pct * 0.35 * trigger_count
            쇄매 = D(expected_pct, VMatrix_Ignore_Guard, 0, 0, Final_Damage)
            state["쇄매"]["times_used"] += 0.35 * 5 * trigger_count
            state["쇄매"]["attacks"] += 0.35 * 15 * trigger_count
            
        # 화중군자 VI   
        화중군자 = 0
        if VI_level[11] > 0:
            if state["화중군자"]["delay"] > 0:
                state["화중군자"]["delay"] -= iteration_time
            if state["화중군자"]["delay"] <= 0:
                pct = (154 + 40 * VI_level[11]) * 7 * 2
                화중군자 = D(pct, Ignore_Guard2, 0, 0, Final_Damage)
                state["화중군자"]["times_used"] += 2
                state["화중군자"]["attacks"] += 14
                state["화중군자"]["delay"] = T_화중군자 - iteration_time
                
        # 오라 웨폰 (펫 버프)
        오라웨폰 = 0
        if state["오라웨폰"]["delay"] > 0:
            state["오라웨폰"]["delay"] -= iteration_time
        if state["오라웨폰"]["delay"] <= 0:
            pct = 1100 * 6
            오라웨폰 = D(pct, Ignore_Guard2, 0, 0, Final_Damage)
            state["오라웨폰"]["times_used"] += 1
            state["오라웨폰"]["attacks"] += 6
            state["오라웨폰"]["delay"] = T_오라웨폰 - iteration_time 
        
        # 만리향
        만리향 = 0
        만리향_active = 1 if Condition_ARRAY[2] <= t % T120 < Condition_ARRAY[2] + 30*1000 + svr_lag else 0
        if 만리향_active == 1:
            if Condition_ARRAY[2] <= t % T120 < Condition_ARRAY[2] + iteration_time:
                state["만리향"]["stack"] = 0
                state["만리향"]["chammae_count"] = 0
            immediate_chammae = (선참_사용 + 섬무_사용 + 일격예인_사용) + (열지_사용*2 + 망탄_사용 + 무량겁_사용*8 + 심검_사용*13 + 승천_사용)
            state["만리향"]["stack"] += (선참_사용 + 섬무_사용 + 일격예인_사용)
            count_from_stack = state["만리향"]["stack"] // 3
            state["만리향"]["stack"] %= 3
            added_count = count_from_stack + (열지_사용*2 + 망탄_사용 + 무량겁_사용*8 + 심검_사용*13 + 승천_사용)
            if immediate_chammae > 0 or added_count > 0:
                old_count = state["만리향"]["chammae_count"]
                state["만리향"]["chammae_count"] += added_count
                new_count = state["만리향"]["chammae_count"]
                blossoms = 0
                if old_count < 30 and new_count >= 30: blossoms += 20
                if old_count < 70 and new_count >= 70: blossoms += 40
                if old_count < 125 and new_count >= 125: blossoms += 65
                total_pct = 0
                total_pct += 380 * 3 * immediate_chammae * VI_level_factor[0]
                if blossoms > 0:
                    total_pct += 500 * 3 * blossoms * VI_level_factor[0]
                만리향 = D(total_pct, Ignore_Guard2, 0, 0, Final_Damage*Grandis_Final_Damage)
                state["만리향"]["times_used"] += immediate_chammae + blossoms
                state["만리향"]["attacks"] += 3 * (immediate_chammae + blossoms)
        else:
            state["만리향"]["stack"] = 0
            state["만리향"]["chammae_count"] = 0
            
        # 망혼각성
        망혼각성 = 0
        망혼각성_active = 1 if Condition_ARRAY[3] <= t % T120 < Condition_ARRAY[3] + 20*1000 + svr_lag else 0
        if 망혼각성_active == 1:
            if Condition_ARRAY[3] <= t % T120 < Condition_ARRAY[3] + iteration_time:
                state["망혼각성"]["stack"] = 0
                state["망혼각성"]["cheona_count"] = 0
            state["망혼각성"]["stack"] += (선참_사용 + 섬무_사용 + 일격예인_사용)
            count_from_stack_v2 = state["망혼각성"]["stack"] // 3
            state["망혼각성"]["stack"] %= 3
            immediate_cheona = count_from_stack_v2 + (열지_사용*2 + 망탄_사용 + 무량겁_사용*8 + 심검_사용*13 + 승천_사용)
            added_count_v2 = count_from_stack_v2 + (열지_사용*2 + 망탄_사용 + 무량겁_사용*8 + 심검_사용*13 + 승천_사용)
            if immediate_cheona > 0 or added_count_v2 > 0:
                old_cheona = state["망혼각성"]["cheona_count"]
                state["망혼각성"]["cheona_count"] += added_count_v2
                new_cheona = state["망혼각성"]["cheona_count"]
                cheongeop_triggered = 0
                if old_cheona < 90 and new_cheona >= 90:
                    cheongeop_triggered = 1
                total_pct_v2 = 0
                total_pct_v2 += (270 + 11 * VI_level[1]) * 2 * immediate_cheona * VI_level_factor[1]
                if cheongeop_triggered:
                    total_pct_v2 += (900 + 35 * VI_level[1]) * 12 * 9 * VI_level_factor[1]
                망혼각성 = D(total_pct_v2, Ignore_Guard2, 0, 0, Final_Damage)
                state["망혼각성"]["times_used"] += immediate_cheona + (9 if cheongeop_triggered else 0)
                state["망혼각성"]["attacks"] += (2 * immediate_cheona) + (108 if cheongeop_triggered else 0)
        else:
            state["망혼각성"]["stack"] = 0
            state["망혼각성"]["cheona_count"] = 0

        # Hecate
        Hecate = 0
        if VI_level[10] > 0 and hecate_lock == 0:
            if state["Hecate"]["delay"] <= 0:
                h_bonus = 20 * min(2, VI_level[10] // 10)
                Hecate = D((374 + 26 * VI_level[10]) * 24, Ignore_Guard2, h_bonus, h_bonus, Final_Damage)
                state["Hecate"]["times_used"] += 4
                state["Hecate"]["attacks"] += 24
                state["Hecate"]["delay"] = 3500 - iteration_time
            else:
                state["Hecate"]["delay"] -= iteration_time
                      
        # 크오솔 & 스인미 (시퀀스 추가 기원)
        elapsed_com = t % T240 - Condition_ARRAY[1]
        CoS, SiM = 0, 0
        if elapsed_com == 0: 
            CoS = D(4223 * 12, Ignore_Guard2, 0, 0, Final_Damage)
            state["CoS"]["times_used"] += 1
            state["CoS"]["attacks"] += 12
            SiM = D(2528 * 15, Ignore_Guard2, 0, 0, Final_Damage)
            state["SiM"]["times_used"] += 1
            state["SiM"]["attacks"] += 15
        if 0 < elapsed_com <= 48300 and elapsed_com % 2100 == 0:
            CoS = D(1541 * 6, Ignore_Guard2, 0, 0, Final_Damage)
            state["CoS"]["times_used"] += 1
            state["CoS"]["attacks"] += 6
        if 0 < elapsed_com <= 49980 and elapsed_com % 8330 == 0: 
            SiM = D(986 * 8 * 5, Ignore_Guard2, 0, 0, Final_Damage)
            state["SiM"]["times_used"] += 5
            state["SiM"]["attacks"] += 40

        skill_values = [
            선참, 섬무, 일격예인, 열지, 망탄, 무량겁, 심검, 망혼강림, 
            영격, 연참, 쇄매, 화중군자, 만리향, 망혼각성,
            승천, 천강, 진천, 낙화, 무량겁_지속,
            오라웨폰, Hecate, Styx, Phlegethon, CoS, SiM, test_graph
        ]

        active_skills = []
        for key, value in zip(skill_order, skill_values):
            state[key]["damage"].append(value)
            if value > 0:
                active_skills.append(key)
                
        if active_skills:
            timeline_log.append((t, active_skills))
    
    Deal = np.vstack([state[name]["damage"] for name in skill_order]) * 4 * (1.3 * 1 * 1.2 * (50 + 5/2)/100 * 1.25 * (1 + 0.86)/2) / (10**12)
    Deal_Cumulative = Deal.sum(axis=1)
    total_sum = Deal_Cumulative.sum()
    Deal_Int = Deal.reshape(len(skill_order), time, 100).sum(axis=2)
    Deal_Int_C = Deal_Int.sum(axis=0)
    Deal_Int_CC = Deal_Int_C.cumsum()
    time_int = np.arange(1, time + 1)
    
    write_skill_log(total_sum, Deal_Cumulative, skill_order, state, 'log.txt')
    #write_timeline_log(timeline_log, 'timeline_log.txt')
    
    jo = int(total_sum // 10**12)
    euk = int((total_sum % 10**12) // 10**8)
    man = int((total_sum % 10**8) // 10**4)
    end_time = tm.time()
    calc_time = end_time - start_time
    print(f"{time/60:.1f}분 딜량 = {jo}조 {euk}억 {man}만")
    #print(f"(연산 소요 시간: {calc_time:.3f}초)")
    draw_graph(plot_graph, time, time_int, Deal_Int, Deal_Int_C, Deal_Int_CC, stats, Deviation=0)

    return total_sum, Deal_Int_C, Deal_Int_CC, time_int


