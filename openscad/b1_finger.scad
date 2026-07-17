// ============================================================
// B1 - 近端指段 (Proximal Phalanx)
// 单位: 毫米 (mm)
//
// 坐标系 (与之前 Fusion 设计保持一致):
//   +X 朝向指尖方向 (长度方向)
//   Y  左右方向 (宽度)
//   Z  上下方向, Z=0 是底面 (手掌侧)
// ============================================================

/* === [全局渲染质量] === */
$fn = 64;

/* === [主壳尺寸] === */
len_x   = 30;     // 指段长度 (X)
wid_y   = 16;     // 指段宽度 (Y)
hgt_z   = 25;     // 指段高度 (Z)

/* === [内腔] === */
wall_x  = 3;      // X 方向壁厚 (前后壁)
wall_y  = 2;      // Y 方向壁厚 (左右壁) -- FDM用2mm
cavity_through = true;

/* === [输出关节孔] === */
joint_r  = 2.65;  // 关节孔半径 -- ⌀5.3 (⌀5金属销 + FDM公差)
joint_z  = 22.5;

/* === [手掌螺丝孔] === */
screw_r     = 1.0;    // 螺丝孔半径 -- ⌀2.0 (M2自攻螺丝)
screw_off_x = 13;
screw_off_y = 6.5;
screw_depth = 5;

// ============================================================
// 模块
// ============================================================

module main_shell() {
    translate([len_x/2, 0, hgt_z/2])
        cube([len_x, wid_y, hgt_z], center = true);
}

module inner_cavity() {
    cavity_h = cavity_through ? (hgt_z + 1) : (hgt_z - 6);
    translate([len_x/2, 0, hgt_z/2])
        cube([
            len_x - 2*wall_x,
            wid_y - 2*wall_y,
            cavity_h
        ], center = true);
}

module joint_hole() {
    translate([len_x, 0, joint_z])
        rotate([0, 90, 0])
        cylinder(h = wall_x + 1, r = joint_r, center = true);
}

module palm_screws() {
    for (sx = [-screw_off_x, screw_off_x],
         sy = [-screw_off_y, screw_off_y])
        translate([len_x/2 + sx, sy, -0.25])
            cylinder(h = screw_depth + 0.5, r = screw_r);
}

// ============================================================
// 组装
// ============================================================

difference() {
    main_shell();
    union() {
        inner_cavity();
        joint_hole();
        palm_screws();
    }
}

echo(str("B1 外形: ", len_x, " x ", wid_y, " x ", hgt_z, " mm"));
echo(str("B1 内腔: ", len_x - 2*wall_x, " x ", wid_y - 2*wall_y, " mm"));
echo(str("关节孔: ", "⌀", joint_r*2, " at Z=", joint_z, " mm"));
echo(str("螺丝孔: ", "⌀", screw_r*2, " x 4"));
