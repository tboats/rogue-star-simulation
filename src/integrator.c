#include <stdio.h>
#include <stdlib.h>
#include <math.h>

void compute_accelerations(const double *pos, const double *gms, int num_bodies, double *acc) {
    for (int i = 0; i < num_bodies; i++) {
        acc[i * 3 + 0] = 0.0;
        acc[i * 3 + 1] = 0.0;
        acc[i * 3 + 2] = 0.0;
        for (int j = 0; j < num_bodies; j++) {
            if (i == j) continue;
            double dx = pos[j * 3 + 0] - pos[i * 3 + 0];
            double dy = pos[j * 3 + 1] - pos[i * 3 + 1];
            double dz = pos[j * 3 + 2] - pos[i * 3 + 2];
            double dist2 = dx * dx + dy * dy + dz * dz;
            double dist = sqrt(dist2);
            double factor = gms[j] / (dist2 * dist);
            acc[i * 3 + 0] += factor * dx;
            acc[i * 3 + 1] += factor * dy;
            acc[i * 3 + 2] += factor * dz;
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 8) {
        printf("Usage: %s <num_bodies> <years> <dt> <save_every> <input_bin> <output_bin> <periods_bin>\n", argv[0]);
        return 1;
    }
    int num_bodies = atoi(argv[1]);
    double years = atof(argv[2]);
    double dt = atof(argv[3]);
    int save_every = atoi(argv[4]);
    const char *input_path = argv[5];
    const char *output_path = argv[6];
    const char *periods_path = argv[7];
    
    double total_days = years * 365.25;
    long long num_steps = (long long)ceil(total_days / dt);
    
    // Allocate arrays
    double *gms = malloc(num_bodies * sizeof(double));
    double *pos = malloc(num_bodies * 3 * sizeof(double));
    double *vel = malloc(num_bodies * 3 * sizeof(double));
    double *acc = malloc(num_bodies * 3 * sizeof(double));
    double *vel_half = malloc(num_bodies * 3 * sizeof(double));
    double *prev_y = malloc(num_bodies * sizeof(double));
    
    if (!gms || !pos || !vel || !acc || !vel_half || !prev_y) {
        printf("Failed to allocate memory.\n");
        return 1;
    }
    
    // Read input binary
    FILE *fin = fopen(input_path, "rb");
    if (!fin) {
        perror("Failed to open input file");
        return 1;
    }
    fread(gms, sizeof(double), num_bodies, fin);
    fread(pos, sizeof(double), num_bodies * 3, fin);
    fread(vel, sizeof(double), num_bodies * 3, fin);
    fclose(fin);
    
    // Open output files
    FILE *fout = fopen(output_path, "wb");
    if (!fout) {
        perror("Failed to open output file");
        return 1;
    }
    
    FILE *f_periods = fopen(periods_path, "wb");
    if (!f_periods) {
        perror("Failed to open periods file");
        fclose(fout);
        return 1;
    }
    
    // Initialize prev_y relative to the Sun (assumed index 0)
    for (int i = 0; i < num_bodies; i++) {
        prev_y[i] = pos[i * 3 + 1] - pos[0 * 3 + 1];
    }
    
    // Initial accelerations
    compute_accelerations(pos, gms, num_bodies, acc);
    
    // Write step 0
    double t_zero = 0.0;
    fwrite(&t_zero, sizeof(double), 1, fout);
    fwrite(pos, sizeof(double), num_bodies * 3, fout);
    fwrite(vel, sizeof(double), num_bodies * 3, fout);
    
    for (long long step = 1; step <= num_steps; step++) {
        // vel_half = vel + 0.5 * acc * dt
        for (int i = 0; i < num_bodies * 3; i++) {
            vel_half[i] = vel[i] + 0.5 * acc[i] * dt;
            pos[i] = pos[i] + vel_half[i] * dt;
        }
        
        compute_accelerations(pos, gms, num_bodies, acc);
        
        // vel = vel_half + 0.5 * acc * dt
        for (int i = 0; i < num_bodies * 3; i++) {
            vel[i] = vel_half[i] + 0.5 * acc[i] * dt;
        }
        
        // Check crossings of y=0 relative to the Sun (index 0)
        for (int i = 1; i < num_bodies; i++) {
            double curr_y = pos[i * 3 + 1] - pos[0 * 3 + 1];
            if (prev_y[i] < 0.0 && curr_y >= 0.0) {
                double frac = -prev_y[i] / (curr_y - prev_y[i]);
                double t_cross = (step - 1) * dt + frac * dt;
                
                // Write body index (i) and crossing time to periods binary
                fwrite(&i, sizeof(int), 1, f_periods);
                fwrite(&t_cross, sizeof(double), 1, f_periods);
            }
            prev_y[i] = curr_y;
        }
        
        if (step % save_every == 0 || step == num_steps) {
            double t_curr = step * dt;
            fwrite(&t_curr, sizeof(double), 1, fout);
            fwrite(pos, sizeof(double), num_bodies * 3, fout);
            fwrite(vel, sizeof(double), num_bodies * 3, fout);
        }
    }
    
    fclose(fout);
    fclose(f_periods);
    free(gms);
    free(pos);
    free(vel);
    free(acc);
    free(vel_half);
    free(prev_y);
    
    return 0;
}
