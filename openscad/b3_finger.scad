// ============================================================
// B3 - 远端指段 / 指尖 (Distal Phalanx)
// 单位: 毫米 (mm)
//
// 坐标系:
//   +X 朝向指尖
//   Y  左右
//   Z  上下, Z=0 是底面
// ============================================================

/* === [全局渲染质量] === */
$fn = 64;

/* === [主壳尺寸] === */
len_x   = 25;
wid_y   = 16;
hgt_z   = 20;

/* === [内腔] === */
wall_x       = 3;
wall_y       = 2;          // Y 方向壁厚 -- FDM用2mm
tip_solid_x  = 5;          // 指尖端实心长度
top_solid_z  = 6;          // 顶部实心高度

/* === [关节孔] -- 只有输入端 === */
joint_r  = 2.65;  // ⌀5.3 (⌀5金属销 + FDM公差)
joint_z  = 18.5;

// ============================================================
// 模块
// ============================================================

module main_shell() {
    translate([len_x/2, 0, hgt_z/2])
        cube([len_x, wid_y, hgt_z], center = true);
}

module inner_cavity() {
    cav_x_start = wall_x;
    cav_x_len   = len_x - wall_x - tip_solid_x;
    cav_y_len   = wid_y - 2*wall_y;
    cav_z_len   = hgt_z - top_solid_z;

    translate([
        cav_x_start + cav_x_len/2,
        0,
        cav_z_len/2
    ])
    cube([cav_x_len, cav_y_len, cav_z_len + 0.5], center = true);
}

module input_joint_hole() {
    translate([0, 0, joint_z])
        rotate([0, 90, 0])
        cylinder(h = wall_x + 1, r = joint_r, center = true);
}

// ============================================================
// 组装
// ============================================================

difference() {
    main_shell();
    union() {
        inner_cavity();
        input_joint_hole();
    }
}

echo(str("B3 外形: ", len_x, " x ", wid_y, " x ", hgt_z, " mm"));
echo(str("B3 内腔: 17 x 12 x 14 mm"));
echo(str("B3 关节孔: ⌀", joint_r*2, " at Z=", joint_z, " mm (仅输入端)"));
