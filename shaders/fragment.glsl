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
