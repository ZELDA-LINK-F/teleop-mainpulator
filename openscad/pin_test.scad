// ============================================================
// pin_test.scad - 配合测试件
// 单位: 毫米 (mm)
//
// 用途:
//   正式打印手指前, 先打这个 ~5 分钟的小件
//   验证 ⌀5.3 的孔对 ⌀5 金属销的松紧是否合适
//
// 打印时间: ~5 分钟
// 耗材: ~2g
// ============================================================

$fn = 64;

/* === [测试孔参数] === */
block_size = 12;       // 方块边长
gap        = 10;       // 两方块间距
test_r     = 2.65;     // 测试孔半径 (⌀5.3)
hole_depth = 12;       // 孔深 = 方块高 (穿透)
pin_r      = 2.5;      // 销钉半径 (可视化)
pin_len    = 22;       // 销钉长度 (可视化, 略短于总宽)

// ============================================================
// 测试块 A (左)
// ============================================================
module block_a() {
    difference() {
        cube([block_size, block_size, block_size], center = true);
        // 中心孔, 沿 X 方向
        rotate([0, 90, 0])
            cylinder(h = hole_depth + 1, r = test_r, center = true);
    }
    // 标签 "A" (用浅槽标记)
    translate([0, 0, block_size/2 + 0.4])
        linear_extrude(0.4)
        text("A", size = 5, halign = "center", valign = "center");
}

// ============================================================
// 测试块 B (右)
// ============================================================
module block_b() {
    difference() {
        cube([block_size, block_size, block_size], center = true);
        rotate([0, 90, 0])
            cylinder(h = hole_depth + 1, r = test_r, center = true);
    }
    translate([0, 0, block_size/2 + 0.4])
        linear_extrude(0.4)
        text("B", size = 5, halign = "center", valign = "center");
}

// ============================================================
// 组装
// ============================================================

// 块 A (左)
translate([-block_size/2 - gap/2, 0, block_size/2])
    block_a();

// 块 B (右)
translate([block_size/2 + gap/2, 0, block_size/2])
    block_b();

// 销钉可视化 (金属销, 蓝色半透明)
color("lightblue", 0.5)
    translate([0, 0, block_size/2])
    rotate([0, 90, 0])
    cylinder(h = pin_len, r = pin_r, center = true);

// ============================================================
// 调试输出
// ============================================================
echo(str("=== 配合测试件 ==="));
echo(str("孔: ⌀", test_r*2, "mm"));
echo(str("销钉: ⌀", pin_r*2, "mm"));
echo(str(""));
echo(str("验证标准:"));
echo(str("  孔太紧 → 下次改 joint_r = 2.7 (⌀5.4)"));
echo(str("  孔太松 → 下次改 joint_r = 2.6 (⌀5.2)"));
echo(str("  刚好合适 → joint_r = 2.65 可用"));
