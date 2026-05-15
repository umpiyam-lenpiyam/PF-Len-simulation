import numpy as np
import time as tm
import math
from PF_cal_function import *
from PF_set_stat import *

def PF_cal_damage_rev2(plot_graph, ring, VI_level, time, print_property, directory):
    start_time = tm.time()
    Boss_Guard = 380
    stats = get_final_stats(directory, print_property, 0)
    ascent_stats = get_final_stats(directory, print_property, 1)
    Condition_ARRAY1, Condition_ARRAY2 = burst_time3()
    VI_level_factor = [calc_vi_factor(lvl) for lvl in VI_level[:4]]
    stats, SharpEyes_Duration, Cardinal_Damage, Additional_Ratio, Additional_Ratio_VI, Cardinal_Attack, Ancient_Enchant_Boss_Damage, Ancient_Enchant_Ignore_Guard, Enchant_Damage = apply_hyper_skills(stats, VI_level)
    T20, T40, T60, T120, T240, T360 = [T(stats, t) for t in (20, 40, 60, 120, 240, 360)]
    
    def D(pct, base_ign, add_boss=0, add_ign=0, f_dmg=1.0):
        return calc_D(pct, base_ign, Boss_Guard, stats, Damage2, Boss_Damage2, Critical_Damage2, DEX2, Attack_Ratio2, add_boss, add_ign, f_dmg)
    
    def Ascent_D(pct, base_ign, add_boss=0, add_ign=0, f_dmg=1.0):
        return calc_Ascent_D(pct, base_ign, Boss_Guard, ascent_stats, add_boss, add_ign, f_dmg)
    
    timeline_log = []
    state = log_array()
    skill_order = list(state.keys())
    svr_lag = stats['Server_Lag'] * 1000
    buff_dur = stats['Buff_Duration']
    Resonance_Num = 1 + stats["Ability_Prob"] / 100
    seed = seed_ring(stats)
    Skill_Lock = 0
    
    Cardinal_between_Delay = Assault_between_delay = Active_Delay = 0
    Discharge_Used = Res_stack = Material_stack = Additional_forbidden = 0
    Additional_Blast_Curse_Arrow = Forsaken_Arrow = Ancient_Fury = 0
    Active = 1
    max_obsidian_stack = int((12 + int(math.ceil(VI_level[2]/4))) / 0.480)
    forsaken_boss_bonus, forsaken_ignore_bonus = get_forsaken_bonus(VI_level[4])
    
    iteration_time = 10 # ms
    for t in range(0*1000,time*1000,iteration_time):
        test_graph = 0      
        keys = ["Damage", "Boss_Damage", "Critical_Prob", "Critical_Damage", "DEX_with_MY", 
                "STR", "Attack_Ratio", "Ignore_Guard", "Real_Attack", "Attack_lumi", "FINAL_ATTACK"]
        (Damage2, Boss_Damage2, Critical_Prob2, Critical_Damage2, DEX2, STR, Attack_Ratio2, 
         Ignore_Guard2, Real_Attack, Attack_lumi, FINAL_ATTACK) = [stats[k] for k in keys]
        VMatrix_Ignore_Guard = Ignore_Guard2 + (100 - Ignore_Guard2) * 0.2
        
        # Penetration (버프 및 링크 반영X 위해 위에 설정)
        Penetration = 0
        if VI_level[9] > 0:
            elapsed_pen = t - 97*1000 #시전 시간 지정
            if 0 <= elapsed_pen <= 6600:
                Skill_Lock = 1 if elapsed_pen < 6600 else 0
                pen_schedule = {0: 6, 2190: 6, 4380: 6, 1500: 19, 3690: 19, 5880: 19}
                if elapsed_pen in pen_schedule:
                    times = pen_schedule[elapsed_pen]
                    attacks = 15 * times
                    pct_penetration = (1288 + 252 * VI_level[9]) * attacks
                    lvl = VI_level[9]
                    pen_boss = 40 + 10 * min(2, lvl // 10)
                    pen_ign  = 60 + 10 * min(2, lvl // 10) + (20 if lvl == 30 else 0)
                    Penetration = Ascent_D(pct_penetration, ascent_stats['Ignore_Guard'], pen_boss, pen_ign)
                    state["Penetration"]["times_used"] += times
                    state["Penetration"]["attacks"] += attacks

 #-----------버프류 설정 구간--------------------------------------------------------------------------------------------------------------------          
        Condition_ARRAY = Condition_ARRAY1 if (t // T120) % 3 == 0 else Condition_ARRAY2       
        Forsaken_buff = 1 if Condition_ARRAY[16] <= (t % T360) <= Condition_ARRAY[16] + 30*1000 + svr_lag else 0
        Ancient_Enchant_Final_Damage = 1.1 * (1.05 + (VI_level[4] // 3) / 100) if Forsaken_buff == 1 else 1.1
        Active_Relic_Evolution = 1 if Condition_ARRAY[13] <= (t % T120) <= Condition_ARRAY[13] + 30*1000 + svr_lag else 0

        if Condition_ARRAY[0] <= (t % T120) <= Condition_ARRAY[0] + 60*1000 + svr_lag: Damage2 += 10 #에픽 어드벤처
        if Condition_ARRAY[3] <= (t % T60)  <  Condition_ARRAY[3] + 10*buff_dur*1000 + svr_lag: Damage2 += seed["Soul_con"]  # 엔버 링크
        if Condition_ARRAY[5] <= (t % (T40+stats["Cool"]*1000))  <  Condition_ARRAY[5] + 20*1000 + svr_lag: Damage2 += 17 # 카인 링크
        if Condition_ARRAY[5] <= (t % (T20+stats["Cool"]*1000))  <  Condition_ARRAY[5] + 10*1000 + svr_lag: Damage2 += 18 # 모도 링크
        if Condition_ARRAY[2] <= (t % T120) < Condition_ARRAY[2] + 30*1000 + svr_lag: #크리인
            Critical_Damage2 += Critical_Prob2 / 2       
        
        # Skill_Active?
        Active = 1 if Active_Delay <= 0 and Skill_Lock == 0 else 0
        Active_Delay -= iteration_time
        
        # 특수 코어 쿨감 X
        if Condition_ARRAY[11] <= t % (120*1000) < Condition_ARRAY[11] + 10*1000:
            if stats["Boss_Slayer"] == 1:   
                Boss_Damage2 += 50
            if stats["Defense_Smash"] == 1: 
                Ignore_Guard2 = VMatrix_Ignore_Guard = 100
        if stats["Fatal_Strike"] == 1 and Condition_ARRAY[12] <= t % (30*1000) < Condition_ARRAY[12] + 4*1000:
            Boss_Damage2 += 100
                  
        Forsaken_ignore = Ignore_Guard2 + (100 - Ignore_Guard2) * forsaken_ignore_bonus
        Forsaken_Boss = Boss_Damage2 + forsaken_boss_bonus

        if t%T120 == 0:
            Evolve_Tempest_Stack = 84
            Relic_Unbound_Stack = 4
            Obsidian_Barrier_Stack = max_obsidian_stack
            Ultimate_Blast_Stack = 1
                                
        # 시드링 
        if ring == 1:
            Damage2 += seed["Continuous_dmg"]
            Attack_Ratio2 += seed["Continuous_att"]
        if Condition_ARRAY[1] <= (t % T120) <= Condition_ARRAY[1] + 60*1000 + svr_lag:
            Damage2 += 20
            DEX2 = stats['MY2_DEX']
            if ring == 1 and Condition_ARRAY[4] <= (t % T120) < Condition_ARRAY[4] + seed["Restraint_time"]*1000:
                Attack_Ratio2 += seed["Restraint_att"]              
#-------------------------------------------------------------------------------------------------------------------------------            
        극딜 = 0 
        # Evolve Tempest
        Evolve_Tempest = 0
        elapsed_tempest = t % T120 - Condition_ARRAY[5]
        if 0 <= elapsed_tempest <= 15000 and Evolve_Tempest_Stack > 0:
            if 0 <= elapsed_tempest <= 540:
                극딜 = 1
            if elapsed_tempest % 120 == 0:
                Evolve_Tempest = D(VI_level_factor[0] * 6000, Ignore_Guard2, Ancient_Enchant_Boss_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                Evolve_Tempest_Stack -= 1
                state["Evolve_Tempest"]["times_used"] += 1
                state["Evolve_Tempest"]["attacks"] += 6
        
        # Relic Unbound
        Relic_Unbound = 0
        elapsed_unbound = t % T120 - (Condition_ARRAY[6] + 500)
        if 0 <= elapsed_unbound <= 20000 and Relic_Unbound_Stack > 0:
            if 0 <= elapsed_unbound <= 540:
                극딜 = 1
            if elapsed_unbound % 2010 == 0:
                Relic_Unbound = D(VI_level_factor[1] * 6 * 1375 * 8, Ignore_Guard2, Ancient_Enchant_Boss_Damage + Enchant_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)                   
                Relic_Unbound_Stack -= 1
                state["Relic_Unbound"]["times_used"] += 6
                state["Relic_Unbound"]["attacks"] += 48
                
        # Obsidian Barrier
        Obsidian_Barrier = 0      
        elapsed_barrier = t % T120 - Condition_ARRAY[7]
        if 0 <= elapsed_barrier <= 25000 and Obsidian_Barrier_Stack > 0:
            if elapsed_barrier % 450 == 0:
                Obsidian_Barrier = D(VI_level_factor[2] * 1270 * 5, Ignore_Guard2, Ancient_Enchant_Boss_Damage + Enchant_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                Obsidian_Barrier_Stack -= 1
                state["Obsidian_Barrier"]["times_used"] += 1
                state["Obsidian_Barrier"]["attacks"] += 5
        
        # Ultimate Blast
        Ultimate_Blast = 0
        elapsed_ultimate = t % T120 - Condition_ARRAY[8]
        if 0 <= elapsed_ultimate <= 840:
            극딜 = 1
        if elapsed_ultimate == 1350:
            Ultimate_Blast = D(VI_level_factor[3] * 6 * 1500 * 15 * 2, 100, Ancient_Enchant_Boss_Damage, 0, Ancient_Enchant_Final_Damage)           
            state["Ultimate_Blast"]["times_used"] += 6
            state["Ultimate_Blast"]["attacks"] += 90
            
        # Forsaken Relic
        Forsaken_Relic = Ancient_Fury = 0
        elapsed_forsaken = t % T360 - Condition_ARRAY[16]
        forsaken_schedule = {
            1500: (775, 26, 9, 22),
            4110: (775, 26, 9, 2),
            4320: (765, 26, 14, 1),
            5310: (765, 26, 14, 4),
            5700: (765, 26, 14, 6),
            6300: (765, 26, 14, 19)}
        if 0 <= elapsed_forsaken <= 6540:
            극딜 = 1
        if elapsed_forsaken == 0:
            state["Ancient_Fury"]["delay"] = 0
        elif elapsed_forsaken in forsaken_schedule:
            base, scale, attacks, times = forsaken_schedule[elapsed_forsaken]
            pct = (base + scale * VI_level[4]) * attacks * times
            Forsaken_Relic = D(pct, Forsaken_ignore, Forsaken_Boss - Boss_Damage2)
            if elapsed_forsaken == 6300:
                state["Forsaken_Relic"]["times_used"] += 54
                state["Forsaken_Relic"]["attacks"] += 636
        else:
            state["Ancient_Fury"]["delay"] -= iteration_time
            
        # Materialize
        Material = 0
        cycle_time = t % T120
        Material_stack += {Condition_ARRAY[5]: 6, Condition_ARRAY[6]: 5, Condition_ARRAY[7]: 6, Condition_ARRAY[8]: 20}.get(cycle_time, 0)
        if Material_stack > 0 and VI_level[8] > 0:
            Material = D(Material_stack * 8 * (730 + 12 * VI_level[8]), Ignore_Guard2)               
            state["Material"]["times_used"] += Material_stack
            state["Material"]["attacks"] += 8 * Material_stack
            Material_stack = 0
         
        # Styx & Phlegethon 
        lvl10 = VI_level[10]
        Styx = 0
        Phlegethon = 0
        hecate_lock = 0
        if lvl10 > 0:
            elapsed_styx = t % T60 - Condition_ARRAY[3] # 엔버 감응
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
                    Styx = D(pct * attacks, Ignore_Guard2, styx_bonus, styx_bonus)
                    state["Styx"]["times_used"] += 1
                    state["Styx"]["attacks"] += attacks
        if lvl10 == 30:
            elapsed_phleg = t % T120 - Condition_ARRAY[4] # 리레 감응
            if 0 <= elapsed_phleg <= 4020:
                hecate_lock = 1
                attacks = 0
                if elapsed_phleg == 960 or (1900 <= elapsed_phleg <= 2980 and elapsed_phleg % 180 == 100):
                    attacks, pct = 4, 1102
                elif 3480 <= elapsed_phleg <= 4020 and elapsed_phleg % 60 == 0:
                    attacks, pct = 6, 877
                if attacks > 0:
                    Phlegethon = D(pct * attacks, Ignore_Guard2, 40, 40)
                    state["Phlegethon"]["times_used"] += 1
                    state["Phlegethon"]["attacks"] += attacks
                    
        Resonance = 0
        Assault = 0
        Resonance2 = 0
        Active_Additional_Discharge = Active_Additional_Blast = 0
        if cycle_time >= Condition_ARRAY[17] and 극딜 == 0:
            # Assault and Resonance VI
            cd_ms = (10 * stats["Cool_R"]) * (1 - 0.05 * stats["Cool"]) * 1000
            Assault = Resonance = Resonance2 = 0
            if VI_level[8] > 0:
                if state["Assault"]["delay"] <= 0 and Active == 1:
                    pct_assault = Resonance_Num * 2.2 * 2* ((775 + 36 * VI_level[8]) * 10 + (700 + 32 * VI_level[8]) * 7)
                    Assault = D(pct_assault, VMatrix_Ignore_Guard, Ancient_Enchant_Boss_Damage + Enchant_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                    state["Assault"]["times_used"] += 4 * Resonance_Num
                    state["Assault"]["attacks"] += 34 * Resonance_Num
                    Assault_between_delay = 510 * Resonance_Num
                    Material_stack += 0.5 * Resonance_Num
                    Additional_forbidden = 1
                    state["Assault"]["delay"] = cd_ms - iteration_time
                    if VI_level[7] > 0:
                        if Res_stack < 2:
                            pct_res = Resonance_Num * 3 * (943 + 33 * VI_level[7]) * 6 * 2.2
                            Resonance = D(pct_res, VMatrix_Ignore_Guard, Ancient_Enchant_Boss_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                            Res_stack += 1
                            state["Resonance"]["attacks"] += 18 * Resonance_Num
                            state["Resonance"]["times_used"] +=  3 * Resonance_Num
                        else:
                            pct_res = Resonance_Num * 3 * (616 + 35 * VI_level[7]) * 10 * 2.2
                            Resonance2 = D(pct_res, VMatrix_Ignore_Guard, Ancient_Enchant_Boss_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                            Res_stack = 0
                            state["Resonance2"]["attacks"] += 30 * Resonance_Num
                            state["Resonance2"]["times_used"] += 3 * Resonance_Num
                    else:
                        pct_res = Resonance_Num * 898 * 3 * 6 * 2.2
                        Resonance = D(pct_res, VMatrix_Ignore_Guard, Ancient_Enchant_Boss_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                        state["Resonance"]["times_used"] +=  3 * Resonance_Num
                        state["Resonance"]["attacks"] += 18 * Resonance_Num
                    Material_stack += 1.5 * Resonance_Num
                    #콤레 이후 블래스트부터 발동
                    Cardinal_between_Delay = 100
                else:
                    Assault_between_delay -= iteration_time
                    state["Assault"]["delay"] -= iteration_time
        else:
            Assault_between_delay -= iteration_time
            state["Assault"]["delay"] -= iteration_time
        
        # 트임
        Triple_Impact = 0
        elapsed_triple = t % T360 - Condition_ARRAY[18]
        if 0 <= elapsed_triple <= 420:
            극딜 = 1
        if elapsed_triple == 420:           
            Triple_Impact = D(2.2*265*3*5, VMatrix_Ignore_Guard)
            Material_stack += 1
            state["Triple_Impact"]["times_used"] +=  3
            state["Triple_Impact"]["attacks"] += 15
        if Condition_ARRAY[19] <= t % T360 < Condition_ARRAY[8]:
            극딜 = 1
        
        Cardinal_Blast = 0
        Cardinal_Discharge = 0
        Cardinal_Transition = 0
        if 극딜 == 0 and cycle_time >= Condition_ARRAY[17]:
            # Cardinal Blast
            if state["Cardinal_Blast"]["delay"] <= 0 and Active == 1 and Assault_between_delay <= 0:
                if VI_level[5] > 0:
                    pct = (569 + 6 * VI_level[5]) * 2.2 * Cardinal_Attack
                else:
                    pct = (520 + 11 * stats["Ability_Passive"]) * 2.2 * Cardinal_Attack
                Cardinal_Blast = D(pct, VMatrix_Ignore_Guard, Cardinal_Damage)
                state["Cardinal_Blast"]["delay"] = 420 - iteration_time
                state["Cardinal_Blast"]["times_used"] += 1
                state["Cardinal_Blast"]["attacks"] += Cardinal_Attack
                Active_Additional_Discharge = 1
                Cardinal_between_Delay = 210 - iteration_time
                Discharge_Used = 0
            else:
                state["Cardinal_Blast"]["delay"] -= iteration_time
                Cardinal_between_Delay -= iteration_time
           
            # Cardinal Discharge
            if state["Cardinal_Discharge"]["delay"] <= 0 and Active == 1 and Cardinal_between_Delay <= 0 and Assault_between_delay <= 0:
                if VI_level[6] > 0:
                    pct = 2 * (299 + 2 * VI_level[6]) * 2.2 * Cardinal_Attack
                else:
                    pct = 2 * (273 + 4 * stats["Ability_Passive"]) * 2.2 * Cardinal_Attack
                Cardinal_Discharge = D(pct, VMatrix_Ignore_Guard, Cardinal_Damage)
                state["Cardinal_Discharge"]["delay"] = 420 - iteration_time
                state["Cardinal_Discharge"]["times_used"] += 2
                state["Cardinal_Discharge"]["attacks"] += 2*Cardinal_Attack
                Active_Additional_Blast = 1
                Discharge_Used = 1
            else:
                state["Cardinal_Discharge"]["delay"] -= iteration_time
            
            # Cardinal Transition (Delay_Example = ms)
            if state["Cardinal_Transition"]["delay"] <= 0 and Active == 1:
                #Cardinal_Transition = D(5(*599+11*VI_level[7]), VMatrix_Ignore_Guard, Cardinal_Damage)
                Cardinal_Transition = D(0, VMatrix_Ignore_Guard, Cardinal_Damage)

                state["Cardinal_Transition"]["delay"] = 300 - iteration_time
            else:
                state["Cardinal_Transition"]["delay"] -= iteration_time
        
        # 포세이큰 마법 화살
        Forsaken_Arrow = 0
        if Forsaken_buff == 1:
            if Condition_ARRAY[16] <= t % T360 <= Condition_ARRAY[16] + (30 + stats["Server_Lag"]) * 1000:
                if Active_Additional_Blast == 1 or Active_Additional_Discharge == 1:
                    pct = (810 + 27 * VI_level[4]) * 5
                    Forsaken_Arrow = D(pct, Forsaken_ignore, Forsaken_Boss - Boss_Damage2)
                    state["Forsaken_Arrow"]["times_used"] += 1
                    state["Forsaken_Arrow"]["attacks"] += 5
                    
            # Ancient Fury
            if Condition_ARRAY[16] <= t % T360 <= Condition_ARRAY[16] + (30+stats["Server_Lag"])*1000:
                if state["Ancient_Fury"]["delay"] <= 0 and (Cardinal_Blast or Cardinal_Discharge or Assault or Triple_Impact) > 0:
                    pct_fury = (650 + 21 * VI_level[4]) * 45
                    Ancient_Fury = D(pct_fury, Forsaken_ignore, forsaken_boss_bonus + Ancient_Enchant_Boss_Damage, Ancient_Enchant_Ignore_Guard, Ancient_Enchant_Final_Damage)
                    fury_cools = max(5000, (7 * stats["Cool_R"]) * (1 - 0.05 * stats["Cool"]) * 1000)
                    state["Ancient_Fury"]["delay"] = fury_cools - iteration_time
                    state["Ancient_Fury"]["times_used"] += 3
                    state["Ancient_Fury"]["attacks"] += 45
                else:
                    Ancient_Fury = 0
        
        # 어썰트 직후 에디셔널 디스차지 발동 X
        if Additional_forbidden and Active_Additional_Discharge:
            Active_Additional_Discharge = Additional_forbidden = 0  
            
        # Additional Blast
        Additional_Blast = 0
        if Active_Additional_Blast == 1 and Active == 1:
            if VI_level[5] > 0:
                arrow_num = (2 + (VI_level[5] // 20)) + (1 if Active_Relic_Evolution == 1 else 0)
                ratio = Additional_Ratio_VI / 100
                base_val = (224 + 2 * VI_level[5]) * 3
                pct = ratio * (base_val + base_val * 0.7 * (arrow_num - 1)) * 2.2
            else:
                arrow_num = 3 if Active_Relic_Evolution == 1 else 2
                ratio = Additional_Ratio / 100
                pct = ratio * (221 + stats["Ability_Passive"]) * 3 * 2.2 * arrow_num
            Additional_Blast = D(pct, VMatrix_Ignore_Guard)
            state["Additional_Blast"]["times_used"] += ratio * arrow_num
            state["Additional_Blast"]["attacks"] += ratio * arrow_num * 3
            Active_Additional_Blast = 0
            
        # Additional Discharge
        Additional_Discharge = 0
        if Active_Additional_Discharge == 1 and Active == 1:
            if VI_level[6] > 0:
                arrow_num = 5 if Active_Relic_Evolution == 1 else 4
                ratio = (Additional_Ratio + 5)/100
                base_val = (147 + 3 * VI_level[6]) * 3
                pct = ratio * (base_val + base_val * 0.7 * (arrow_num - 1)) * 2.2
            else:
                arrow_num = 4 if Active_Relic_Evolution == 1 else 3
                ratio = Additional_Ratio / 100
                pct = ratio * (166 + stats["Ability_Passive"]) * 3 * 2.2 * arrow_num
            Additional_Discharge = D(pct, VMatrix_Ignore_Guard)
            state["Additional_Discharge"]["times_used"] += ratio * arrow_num
            state["Additional_Discharge"]["attacks"] += ratio * arrow_num * 3
            Active_Additional_Discharge = 0
            
        # Additional Blast Curse Arrow
        Additional_Blast_Curse_Arrow = 0
        if VI_level[5] > 0:
            if state["Additional_Blast_Curse_Arrow"]["delay"] <= 0 and (Cardinal_Blast or Cardinal_Discharge) > 0:
                arrows = 6 + (VI_level[5] // 3)
                pct = arrows * (120 + 2 * VI_level[5]) * 4 * 2.2
                Additional_Blast_Curse_Arrow = D(pct, VMatrix_Ignore_Guard)
                state["Additional_Blast_Curse_Arrow"]["times_used"] += arrows
                state["Additional_Blast_Curse_Arrow"]["attacks"] += arrows * 4
                state["Additional_Blast_Curse_Arrow"]["delay"] = (20*stats["Cool_R"] - stats["Cool"]) * 1000 - iteration_time
            else:
                state["Additional_Blast_Curse_Arrow"]["delay"] -= iteration_time

        # Raven 
        Raven = 0
        raven_start = Condition_ARRAY[14] + (40 + stats["Server_Lag"]) * 1000
        raven_end = Condition_ARRAY[14] + T120
        if raven_start <= cycle_time < raven_end:
            if state["Raven"]["delay"] <= 0:
                if VI_level[8] > 0:
                    pct = 2.80 * (435 + 5 * VI_level[8])
                    interval = 3000
                else:
                    pct = 2.80 * 390
                    interval = 1700
                Raven = D(pct, VMatrix_Ignore_Guard)
                state["Raven"]["times_used"] += 1
                state["Raven"]["attacks"] += 1
                state["Raven"]["delay"] = interval - iteration_time
            else:
                state["Raven"]["delay"] -= iteration_time
        else:
            state["Raven"]["delay"] = 0
            
        # Evolve & Evolve VI (Orbit)
        Evolve = Evolve_Orbit = 0
        lvl11 = VI_level[11]
        if lvl11 > 0:
            elapsed_evolve = t % T120 - Condition_ARRAY[14]
            if 0 <= elapsed_evolve <= 40000 + stats["Server_Lag"] * 1000:
                if elapsed_evolve <= 3500 and elapsed_evolve % 500 == 0:
                    Evolve_Orbit = D((759 + 38 * lvl11) * 8, Ignore_Guard2)
                    state["Evolve_Orbit"]["times_used"] += 1
                    state["Evolve_Orbit"]["attacks"] += 8
                elif 4000 <= elapsed_evolve <= 37000 and elapsed_evolve % 3000 == 1000:
                    Evolve = D((1150 + 58 * lvl11) * 11, Ignore_Guard2)
                    state["Evolve"]["times_used"] += 1
                    state["Evolve"]["attacks"] += 11
        else:
            evolve_start = Condition_ARRAY[14]
            evolve_end = Condition_ARRAY[14] + (40 + stats["Server_Lag"]) * 1000
            if evolve_start <= cycle_time < evolve_end:
                elapsed_evolve2 = cycle_time - evolve_start
                if elapsed_evolve2 % 3650 == 0:
                    Evolve = D(900 * 7, Ignore_Guard2)
                    state["Evolve"]["times_used"] += 1
                    state["Evolve"]["attacks"] += 7 
                    
        # Guided Arrow
        Guided_Arrow = 0
        guided_interval = 310  # 보스 사이즈에 따라 변경
        if t % guided_interval == 0:
            Guided_Arrow = D(880, Ignore_Guard2)                
            state["Guided_Arrow"]["times_used"] += 1
            state["Guided_Arrow"]["attacks"] += 1
            
        # Hecate
        Hecate = 0
        if VI_level[10] > 0 and hecate_lock == 0:
            if state["Hecate"]["delay"] <= 0:
                h_bonus = 20 * min(2, VI_level[10] // 10)
                Hecate = D((374 + 26 * VI_level[10]) * 24, Ignore_Guard2, h_bonus, h_bonus)
                state["Hecate"]["times_used"] += 4
                state["Hecate"]["attacks"] += 24
                state["Hecate"]["delay"] = 3500 - iteration_time
            else:
                state["Hecate"]["delay"] -= iteration_time
                
        # 크오솔 & 스인미 (시퀀스 추가 기원)
        elapsed_com = t % T240 - Condition_ARRAY[1]
        CoS, SiM = 0, 0
        if elapsed_com == 0: 
            CoS = D(4223 * 12, Ignore_Guard2)
            state["CoS"]["times_used"] += 1
            state["CoS"]["attacks"] += 12
            SiM = D(2528 * 15, Ignore_Guard2)
            state["SiM"]["times_used"] += 1
            state["SiM"]["attacks"] += 15
        if 0 < elapsed_com <= 48300 and elapsed_com % 2100 == 0:
            CoS = D(1541 * 6, Ignore_Guard2)
            state["CoS"]["times_used"] += 1
            state["CoS"]["attacks"] += 6
        if 0 < elapsed_com <= 49980 and elapsed_com % 8330 == 0: 
            SiM = D(986 * 8 * 5, Ignore_Guard2)
            state["SiM"]["times_used"] += 5
            state["SiM"]["attacks"] += 40

        skill_values = [
            Cardinal_Blast, Cardinal_Discharge, Cardinal_Transition,
            Additional_Blast, Additional_Discharge, Resonance, 
            Triple_Impact, Raven, Guided_Arrow, Ultimate_Blast,
            Evolve_Tempest, Obsidian_Barrier, Relic_Unbound, Evolve,
            Forsaken_Relic, Additional_Blast_Curse_Arrow, Forsaken_Arrow,
            Ancient_Fury, Material, Resonance2, Assault,
            Hecate, Styx, Phlegethon, Penetration, CoS, SiM, Evolve_Orbit, test_graph
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
    
    write_skill_log(total_sum, Deal_Cumulative, skill_order, state, 'PF_log.txt')
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


