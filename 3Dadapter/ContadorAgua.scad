difference() {
    union() {
        
        color([1, 0, 0])
        linear_extrude(2)
        difference() {
            translate([-8, -7, 0])
                circle(32);
            translate([12, -10, 0])
                circle(7);
        }
        // Apoios para parafusos
        difference() {
            color([1, 0, 0]) {
                
                translate([-2.5, 17.5, 0]) 
                    minkowski() {
                        cylinder(h=2.5, r=6);
                        cube([6,6,.8]);
                    }
                translate([20, 17.5, 0])
                    minkowski() {
                        cylinder(h=2.5, r=6);
                        cube([6,6,.8]);
                    }
            }
            union() {
                translate([23, 11.5,0])
                    cube([40, 40, 4]);
                translate([0, 23,0])
                    cube([40, 20, 4]);
                }
        }
        //Fechar ponta do sensor no semi circulo
        translate([9, 11, 0])
                cube([14, 12, 2]);

        //Reforço cilindro Externo
        translate([19, -7, 0])
                cube([4.5, 30, 2]);

        // Abraço do sensor
        color([0, 0, 0])
        translate([1, -10, 2])
            cube([4, 10, 10]);
    }
    // Remover resto do cilindro
    translate([-79, -50, -1]) {
        cube([80, 100, 10]);
    }
    
    // Parafusos
    color([1, 0, 0])
    union() {
        translate([5.2,16.5, -0.005])
        cylinder(h=7, r1=1.6, r2=4);
        
        translate([18,16.5, 1])
        cylinder(h=3, r1=1.6, r2=1);
        
        translate([15.8, -19.5, -5])
        cylinder(h=10, r1=1.6, r2=1.6);
    };

    //Corpo do Sensor
    translate([3, -11, -1])
    color([0, 0, 1])
        cube([18.5, 22.5, 11.5]);
}