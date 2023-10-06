import os
import typing as t

import imgui
import moderngl
import moderngl_window as mglw
import numpy as np
from moderngl_window.integrations.imgui import ModernglWindowRenderer


class Example(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Mandelbrot Revisited (by h3nnn4n)"
    window_size = (1280, 720)
    aspect_ratio = 16 / 9
    resizable = True

    resource_dir = os.path.normpath(os.path.join(__file__, "../assets/"))


class Fractal(Example):
    title = "Mandelbrot"
    gl_version = (3, 3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.wnd)
        self.imgui_io = imgui.get_io()

        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330

                in vec2 in_vert;
                out vec2 v_text;

                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_text = in_vert;
                }
            """,
            fragment_shader="""
                #version 330

                in vec2 v_text;
                out vec4 f_color;

                uniform sampler2D Texture;
                uniform vec2 Center;
                uniform float Scale;
                uniform float Ratio;
                uniform int Iter;

                void main() {
                    vec2 c;
                    float p;
                    int i;

                    c.x = Ratio * v_text.x * Scale - Center.x;
                    c.y = v_text.y * Scale - Center.y;

                    vec2 z = c;

                    for (i = 0; i < Iter; i++) {
                        float x = (z.x * z.x - z.y * z.y) + c.x;
                        float y = (z.y * z.x + z.x * z.y) + c.y;

                        if ((x * x + y * y) > 4.0) {
                            break;
                        }

                        z.x = x;
                        z.y = y;
                    }

                    if (i == Iter) {
                        f_color = vec4(0, 0, 0, 1);
                    } else {
                        p = float(i);
                        p += 1.0 - log(log(length(z))) / log(2.0);
                        p /= float(Iter);

                        f_color = texture(Texture, vec2(p, 0.0));
                    }
                }
            """,
        )

        self.center = self.prog["Center"]
        self.scale = self.prog["Scale"]
        self.ratio = self.prog["Ratio"]
        self.iter = self.prog["Iter"]

        self.texture = self.load_texture_2d("pal.png")

        vertices = np.array([-1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0])

        self.vbo = self.ctx.buffer(vertices.astype("f4"))
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, "in_vert")

        self.center.value = (0.5, 0.0)
        self.iter.value = 100
        self.scale.value = 1.5

        self.mouse_position: t.Tuple[int, int] = (0, 0)

    def render(self, time, frame_time):
        self.time = time
        self.frame_time = frame_time

        self.ctx.clear(1.0, 1.0, 1.0)
        self.ratio.value = self.aspect_ratio

        self.texture.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)

        self.render_ui()

    def render_ui(self):
        frame_time_ms = self.frame_time * 1000
        fps = 1.0 / self.frame_time

        imgui.new_frame()

        # FPS

        imgui.begin("Config", True)

        imgui.text("Hello fractal world!")
        imgui.text(f"fps: {fps:5.2f} ({frame_time_ms:.2f}ms)")

        imgui.end()

        # Position

        imgui.begin("Position", True)

        scale = self.scale.value
        center = self.center.value
        center_x = center[0]
        center_y = center[1]

        changed, value = imgui.slider_int("iterations", self.iter.value, min_value=0, max_value=2048, format="%d")
        if changed:
            self.iter.value = value

        imgui.text(f"center: {center_x} {center_y}")
        imgui.text(f"real: {center_x - scale} {center_x + scale}")
        imgui.text(f"imag: {center_y - scale} {center_y + scale}")
        imgui.text(f"scale: {scale}")
        imgui.text(f"ratio: {self.ratio.value}")

        imgui.end()

        # Mouse

        imgui.begin("Mouse", True)

        mouse_fractal_position = self._screen_to_fractal_position(self.mouse_position)
        imgui.text(f"  mouse: {self.mouse_position}")
        imgui.text(f"fractal: {mouse_fractal_position}")

        imgui.end()

        # End

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def _screen_to_fractal_position(self, position: t.Tuple[int | float, int | float]) -> t.Tuple[float, float]:
        p_x, p_y = position
        screen_width, screen_height = self.window_size

        scale = self.scale.value
        fcenter_x, fcenter_y = self.center.value
        fx_min = fcenter_x - scale
        fy_min = fcenter_y - scale

        f_x = (1.0 - (p_x / screen_width)) * (scale * 2.0) + fx_min
        f_y = (p_y / screen_height) * (scale * 2.0) + fy_min

        return (f_x, f_y)

    # Event Handlers

    def resize(self, width: int, height: int):
        self.imgui.resize(width, height)

    def key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.mouse_position = (x, y)
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        # Maybe use dragging tomove around instead of clicking?
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

        if y_offset > 0:
            self.scale.value *= 1.05

        if y_offset < 0:
            self.scale.value *= 0.95

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)

        if self.imgui_io.want_capture_mouse:
            return

        mouse_fractal_position = self._screen_to_fractal_position((x, y))
        self.center.value = mouse_fractal_position

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)


if __name__ == "__main__":
    Fractal.run()
