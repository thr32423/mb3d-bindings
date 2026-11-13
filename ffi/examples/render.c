/* A picture from C.
 *
 *     cargo build --release                      (in ffi/)
 *     cc examples/render.c -Iinclude -Ltarget/release -lmb3d -o render
 *     LD_LIBRARY_PATH=target/release ./render [file.m3p]
 */
#include <stdio.h>
#include "mb3d.h"

static int progress(void *user, const char *stage, size_t done, size_t total) {
    (void)user;
    fprintf(stderr, "\r%s %3zu %%   ", *stage ? stage : "calculating", total ? 100 * done / total : 0);
    return 0; /* non-zero would stop the calculation */
}

int main(int argc, char **argv) {
    mb3d_scene *scene = argc > 1 ? mb3d_open(argv[1]) : mb3d_preset("Amazing Box");
    if (!scene) {
        fprintf(stderr, "%s\n", mb3d_last_error());
        return 1;
    }
    mb3d_use_gpu(1);
    if (mb3d_scene_set(scene, "iterations = 12") != 0) {
        fprintf(stderr, "%s\n", mb3d_last_error());
    }
    mb3d_scene_resize(scene, 1280, 960);

    mb3d_picture *picture = mb3d_render(scene, progress, NULL);
    if (!picture) {
        fprintf(stderr, "\n%s\n", mb3d_last_error());
        mb3d_scene_free(scene);
        mb3d_finish();
        return 1;
    }
    const uint8_t *rgb = mb3d_picture_rgb(picture);
    fprintf(stderr, "\n%u x %u in %.2f s; the first pixel is %u, %u, %u\n", mb3d_picture_width(picture), mb3d_picture_height(picture),
            mb3d_picture_seconds(picture), rgb[0], rgb[1], rgb[2]);
    if (mb3d_picture_save_png(picture, "picture.png") != 0) {
        fprintf(stderr, "%s\n", mb3d_last_error());
    } else {
        printf("picture.png\n");
    }
    mb3d_picture_free(picture);
    mb3d_scene_free(scene);
    mb3d_finish();
    return 0;
}
