// ============================================================
// B2 - 中段指段 (Middle Phalanx)
// 单位: 毫米 (mm)
//
// 坐标系:
//   +X 朝向指尖 (长度方向)
//   Y  左右 (宽度)
//   Z  上下, Z=0 是底面
// ============================================================

/* === [全局渲染质量] === */
$fn = 64;

/* === [主壳尺寸] === */
len_x   = 30;
wid_y   = 16;
hgt_z   = 25;

/* === [内腔] === */
wall_x  = 3;
wall_y  = 2;      // Y 方向壁厚 -- FDM用2mm
cavity_through = true;

/* === [关节孔] -- 两端都有 === */
joint_r  = 2.65;  // ⌀5.3 (⌀5金属销 + FDM公差)
joint_z  = 22.5;

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

module input_joint_hole() {
    translate([0, 0, joint_z])
        rotate([0, 90, 0])
        cylinder(h = wall_x + 1, r = joint_r, center = true);
}

module output_joint_hole() {
    translate([len_x, 0, joint_z])
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
        output_joint_hole();
    }
}

echo(str("B2 外形: ", len_x, " x ", wid_y, " x ", hgt_z, " mm"));
echo(str("B2 关节孔: ⌀", joint_r*2, " at Z=", joint_z, " mm, 两端"));
