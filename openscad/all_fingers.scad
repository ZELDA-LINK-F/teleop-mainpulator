// ============================================================
// all_fingers.scad - 整根手指预览 (B1 + B2 + B3 串联)
// 单位: 毫米 (mm)
//
// 用法:
//   - 在 OpenSCAD 打开这个文件 (而不是 b1/b2/b3 单独的)
//   - F5 预览, 能看到 3 个指段如何拼成一整根手指
//   - F6 渲染后 File > Export > Export as STL 导出整指
//
// 拼装方式:
//   - B1: X[0, 30]   手掌端有 4 螺丝, 末端有 ⌀5 关节孔
//   - B2: X[30, 60]  两端都是 ⌀5 关节孔
//   - B3: X[60, 85]  输入端有 ⌀5 关节孔, 输出端是实心指尖
//
// 实际装配时:
//   - ⌀5 的轴贯穿: B1.输出 → B2.输入 → B2.输出 → B3.输入
//   - 4 颗 M2 螺丝把 B1 锁在手掌板上
//   - 关节处可以加扭簧 (提供回弹力) 或连到舵机 (主动驱动)
// ============================================================

/* === [全局] === */
$fn = 64;

/* === [B1 参数] === */
b1_len   = 30;
b1_wid   = 16;
b1_hgt   = 25;
b1_wall_x = 3;
b1_wall_y = 1;
b1_joint_r = 2.5;
b1_joint_z = 22.5;
b1_screw_r = 0.85;
b1_screw_off_x = 13;
b1_screw_off_y = 6.5;
b1_screw_depth = 5;

/* === [B2 参数] === */
b2_len   = 30;
b2_wid   = 16;
b2_hgt   = 25;
b2_wall_x = 3;
b2_wall_y = 1;
b2_joint_r = 2.5;
b2_joint_z = 22.5;

/* === [B3 参数] === */
b3_len   = 25;
b3_wid   = 16;
b3_hgt   = 20;
b3_wall_x = 3;
b3_wall_y = 1;
b3_joint_r = 2.5;
b3_joint_z = 18.5;
b3_tip_solid_x = 5;
b3_top_solid_z = 6;

// ============================================================
// 段模块 (复用 3 次, 每次不同位置)
// ============================================================

module b1_finger() {
    difference() {
        translate([b1_len/2, 0, b1_hgt/2])
            cube([b1_len, b1_wid, b1_hgt], center = true);
        union() {
            translate([b1_len/2, 0, b1_hgt/2])
                cube([b1_len - 2*b1_wall_x,
                      b1_wid - 2*b1_wall_y,
                      b1_hgt + 1], center = true);
            translate([b1_len, 0, b1_joint_z])
                rotate([0, 90, 0])
                cylinder(h = b1_wall_x + 1, r = b1_joint_r, center = true);
            for (sx = [-b1_screw_off_x, b1_screw_off_x],
                 sy = [-b1_screw_off_y, b1_screw_off_y])
                translate([b1_len/2 + sx, sy, -0.25])
                    cylinder(h = b1_screw_depth + 0.5, r = b1_screw_r);
        }
    }
}

module b2_finger() {
    difference() {
        translate([b2_len/2, 0, b2_hgt/2])
            cube([b2_len, b2_wid, b2_hgt], center = true);
        union() {
            translate([b2_len/2, 0, b2_hgt/2])
                cube([b2_len - 2*b2_wall_x,
                      b2_wid - 2*b2_wall_y,
                      b2_hgt + 1], center = true);
            translate([0, 0, b2_joint_z])
                rotate([0, 90, 0])
                cylinder(h = b2_wall_x + 1, r = b2_joint_r, center = true);
            translate([b2_len, 0, b2_joint_z])
                rotate([0, 90, 0])
                cylinder(h = b2_wall_x + 1, r = b2_joint_r, center = true);
        }
    }
}

module b3_finger() {
    difference() {
        translate([b3_len/2, 0, b3_hgt/2])
            cube([b3_len, b3_wid, b3_hgt], center = true);
        union() {
            cav_x_start = b3_wall_x;
            cav_x_len   = b3_len - b3_wall_x - b3_tip_solid_x;
            cav_y_len   = b3_wid - 2*b3_wall_y;
            cav_z_len   = b3_hgt - b3_top_solid_z;
            translate([cav_x_start + cav_x_len/2, 0, cav_z_len/2])
                cube([cav_x_len, cav_y_len, cav_z_len + 0.5], center = true);
            translate([0, 0, b3_joint_z])
                rotate([0, 90, 0])
                cylinder(h = b3_wall_x + 1, r = b3_joint_r, center = true);
        }
    }
}

// ============================================================
// 装配: 把 3 段串起来
// ============================================================

b1_finger();
translate([b1_len, 0, 0])
    b2_finger();
translate([b1_len + b2_len, 0, 0])
    b3_finger();

echo(str("=== 整指规格 ==="));
echo(str("总长: ", b1_len + b2_len + b3_len, " mm"));
echo(str("总宽: ", b1_wid, " mm (整段一致)"));
echo(str("总高: 不一致 -- B1/B2=25, B3=20"));
echo(str("关节孔: ⌀", b1_joint_r*2, " 共 4 个 (B1→B2 两端, B2→B3 两端)"));
echo(str("螺丝孔: ⌀", b1_screw_r*2, " 共 4 个 (B1 手掌端)"));

/* ============================================================
 * 怎么把这根手指"立起来":
 *
 *   OpenSCAD 默认 Y 轴朝"里", Z 轴朝上.
 *   手指现在躺在 XY 平面上, Z=0 是底面.
 *
 *   要打印时手指立着 (Z 朝上), 不需要任何变换 --
 *   OpenSCAD 导出的 STL 用切片软件 (Cura) 打开后,
 *   默认 Z 就是垂直方向, 跟我们这里一致.
 *
 *   但如果你想预览时"手指站起来", 可以加:
 *     rotate([0, -90, 0])  // 让 X 轴朝上
 *   试试看效果.
 * ============================================================ */