// ============================================================
// all_fingers.scad - 整根手指预览 (B1 + B2 + B3 串联 + 销钉)
// 单位: 毫米 (mm)
//
// 用法:
//   - 在 OpenSCAD 打开这个文件 → F5 预览
//   - 改 angle1 / angle2 看弯曲效果 → F5 刷新
//   - F6 渲染 → File > Export > Export as STL
//
// 弯曲预览:
//   改文件顶部的 angle1=30; angle2=30; 然后 F5
//   手指就会弯成钩状, 模拟抓握姿势
// ============================================================

/* === [全局] === */
$fn = 64;

/* === [显示开关] === */
show_pins  = true;
angle1     = 0;       // B2相对于B1的转角(°), 正=下弯, 试试30
angle2     = 0;       // B3相对于B2的转角(°), 正=下弯, 试试30

/* === [B1 参数] === */
b1_len     = 30;
b1_wid     = 16;
b1_hgt     = 25;
b1_wall_x  = 3;
b1_wall_y  = 2;       // FDM用2mm
b1_joint_r = 2.65;    // 5.3 金属销+公差异
b1_joint_z = 22.5;
b1_screw_r = 1.0;     // 2.0 M2自攻
 
screw_off_x = 13;
screw_off_y = 6.5;
screw_depth = 5;

/* === [B2 参数] === */
b2_len     = 30;
b2_wid     = 16;
b2_hgt     = 25;
b2_wall_x  = 3;
b2_wall_y  = 2;
b2_joint_r = 2.65;
b2_joint_z = 22.5;

/* === [B3 参数] === */
b3_len       = 25;
b3_wid       = 16;
b3_hgt       = 20;
b3_wall_x    = 3;
b3_wall_y    = 2;
b3_joint_r   = 2.65;
b3_joint_z   = 18.5;
tip_solid    = 5;
top_solid    = 6;

/* === [销钉参数] === */
pin_r   = 2.5;
pin_len = 18;
pin_y   = 5.5;

// ============================================================
// B1 段 (手掌端固定)
// ============================================================
module b1_segment() {
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
            for (sx = [-screw_off_x, screw_off_x],
                 sy = [-screw_off_y, screw_off_y])
                translate([b1_len/2 + sx, sy, -0.25])
                    cylinder(h = screw_depth + 0.5, r = b1_screw_r);
        }
    }
}

// ============================================================
// B2 段 (中间段, 两关节)
// ============================================================
module b2_segment() {
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

// ============================================================
// B3 段 (指尖)
// ============================================================
module b3_segment() {
    difference() {
        translate([b3_len/2, 0, b3_hgt/2])
            cube([b3_len, b3_wid, b3_hgt], center = true);
        union() {
            cx0 = b3_wall_x;
            cxl = b3_len - b3_wall_x - tip_solid;
            cyl = b3_wid - 2*b3_wall_y;
            czl = b3_hgt - top_solid;
            translate([cx0 + cxl/2, 0, czl/2])
                cube([cxl, cyl, czl + 0.5], center = true);
            translate([0, 0, b3_joint_z])
                rotate([0, 90, 0])
                cylinder(h = b3_wall_x + 1, r = b3_joint_r, center = true);
        }
    }
}

// ============================================================
// 销钉可视化 (蓝色半透明, 纯预览)
// ============================================================
module axle_pin(x_pos, z_pos) {
    for (py = [-pin_y, pin_y]) {
        translate([x_pos, py, z_pos])
            rotate([0, 90, 0])
            color("lightblue", 0.6)
            cylinder(h = pin_len, r = pin_r, center = true);
    }
}

// ============================================================
// 装配 — 支持弯曲预览
// ============================================================

// B1 固定
b1_segment();

// B2 绕 Joint1 (X=b1_len) 旋转 angle1
translate([b1_len, 0, 0])
    rotate([0, 0, angle1]) {
        b2_segment();
        // B3 绕 Joint2 (B2末端) 旋转 angle2
        translate([b2_len, 0, 0])
            rotate([0, 0, angle2])
                b3_segment();
    }

// 销钉 (平直位置, 预览用)
if (show_pins) {
    axle_pin(b1_len, b1_joint_z);
    axle_pin(b1_len + b2_len, b2_joint_z);
}

echo(str("===== 整指规格 ====="));
echo(str("总长(平直): ", b1_len + b2_len + b3_len, " mm"));
echo(str("关节1转角: ", angle1, " 度"));
echo(str("关节2转角: ", angle2, " 度"));
echo(str(""));
echo(str("提示: 把 angle1 和 angle2 改成 30~45 看弯曲效果"));
