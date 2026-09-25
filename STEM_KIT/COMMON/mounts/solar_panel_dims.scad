// shared solar-panel frame dimensions (included by frame + tilt bracket)
sp_pocket   = [solar_panel_size[0] + solar_panel_clear, solar_panel_size[1] + solar_panel_clear, solar_panel_size[2] + 0.3];
sp_wall     = 3;
sp_back     = 4;
sp_lip      = 2;
sp_outer    = [sp_pocket[0] + 2 * sp_wall, sp_pocket[1] + 2 * sp_wall, sp_back + sp_pocket[2] + sp_lip];
sp_boss_len = 8;
sp_boss_r   = 6;
sp_boss_z   = 6;
sp_boss_end = sp_outer[0] / 2 + sp_boss_len;
