import reflex as rx
import sympy
from sympy import symbols, sympify, limit, oo, latex

x_sym = symbols('x')

MATHJAX_SCRIPT_HTML = """
<script type="text/javascript" id="MathJax-script" async
    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
</script>
<script>
  if (window.MathJax) {
    window.MathJax.startup = {
      ready: () => {
        window.MathJax.startup.defaultReady();
        const observer = new MutationObserver((mutationsList, observer) => {
          for(const mutation of mutationsList) {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
              if (typeof MathJax.typesetPromise === 'function') {
                MathJax.typesetPromise();
              }
              break; 
            }
          }
        });
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      }
    };
  }
</script>
"""

class State(rx.State):
    funcion_str: str = "(x**2 - 1) / (x - 1)"
    punto_x_str: str = "1"
    resultado_analisis: str = ""
    funcion_redefinida_latex: str = ""

    def _parse_input(self, expr_str, val_str):
        try:
            expr_str_sympy = expr_str.replace('^', '**').replace('ln(', 'log(')
            func = sympify(expr_str_sympy)
        except (SyntaxError, TypeError, sympy.SympifyError) as e:
            return None, None, f"Error al parsear la función: {str(e)}"
        try:
            if val_str.lower() == 'oo':
                punto = oo
            elif val_str.lower() == '-oo':
                punto = -oo
            else:
                punto = sympify(val_str)
                if not punto.is_Number:
                    raise ValueError("El punto x debe ser un valor numérico o oo / -oo.")
        except (SyntaxError, TypeError, sympy.SympifyError, ValueError) as e:
            return func, None, f"Error al parsear el punto x: {str(e)}"
        return func, punto, None

    def analizar_funcion_event(self):
        self.resultado_analisis = ""
        self.funcion_redefinida_latex = ""

        if not self.funcion_str.strip() or not self.punto_x_str.strip():
            self.resultado_analisis = "Por favor, ingrese una función y un valor para x."
            return

        func, punto_eval, error_msg = self._parse_input(self.funcion_str, self.punto_x_str)

        if error_msg:
            self.resultado_analisis = error_msg
            return
        if func is None or punto_eval is None:
            self.resultado_analisis = "Error interno al parsear la entrada."
            return

        try:
            valor_en_punto = func.subs(x_sym, punto_eval)
        except Exception:
            valor_en_punto = sympy.nan
        try:
            lim_en_punto = limit(func, x_sym, punto_eval)
        except Exception as e:
            self.resultado_analisis = f"No se pudo calcular el límite en x=${latex(punto_eval)}$: {str(e)}"
            return
        try:
            lim_izquierda = limit(func, x_sym, punto_eval, dir='-')
            lim_derecha = limit(func, x_sym, punto_eval, dir='+')
        except Exception:
            lim_izquierda = lim_derecha = sympy.nan

        f_a_definida = valor_en_punto.is_finite
        lim_existe_y_finito = lim_en_punto.is_finite
        
        punto_eval_latex = latex(punto_eval) 
        mensaje = f"Análisis para $f(x) = {latex(func)}$ en $x = {punto_eval_latex}$:\n"
        sub_general_str = f"x \\to {punto_eval_latex}"
        sub_izquierda_str = f"x \\to {punto_eval_latex}^-"
        sub_derecha_str = f"x \\to {punto_eval_latex}^+"

        if f_a_definida and lim_existe_y_finito and valor_en_punto == lim_en_punto:
            mensaje += f"✅ La función es **CONTINUA** en $x = {punto_eval_latex}$.\n"
            mensaje += f"$f({punto_eval_latex}) = {latex(valor_en_punto)}$ y $\\lim_{{{sub_general_str}}} f(x) = {latex(lim_en_punto)}$."
        else:
            mensaje += f"❌ La función es **DISCONTINUA** en $x = {punto_eval_latex}$.\n"
            mensaje += f"$f({punto_eval_latex}) = {latex(valor_en_punto)}$\n"
            mensaje += f"$\\lim_{{{sub_general_str}}} f(x) = {latex(lim_en_punto)}$\n"
            mensaje += f"$\\lim_{{{sub_izquierda_str}}} f(x) = {latex(lim_izquierda)}$\n"
            mensaje += f"$\\lim_{{{sub_derecha_str}}} f(x) = {latex(lim_derecha)}$\n"

            if lim_existe_y_finito:
                mensaje += "**Tipo:** Discontinuidad EVITABLE\n"
                f_redefinida = sympy.Piecewise((lim_en_punto, sympy.Eq(x_sym, punto_eval)), (func, True))
                self.funcion_redefinida_latex = latex(f_redefinida)
                mensaje += f"Redefinición posible:\n$g(x) = {self.funcion_redefinida_latex}$"
            else:
                if lim_izquierda.is_finite and lim_derecha.is_finite and lim_izquierda != lim_derecha:
                    mensaje += "**Tipo:** Discontinuidad NO EVITABLE (de salto)\n"
                elif abs(lim_en_punto) == oo or abs(lim_izquierda) == oo or abs(lim_derecha) == oo:
                    mensaje += "**Tipo:** Discontinuidad NO EVITABLE (infinita)\n"
                else:
                    mensaje += "**Tipo:** Discontinuidad NO EVITABLE (esencial)\n"

        self.resultado_analisis = mensaje

def index() -> rx.Component:
    return rx.fragment(
        rx.html(MATHJAX_SCRIPT_HTML),
        rx.center(
            rx.vstack(
                rx.heading("Reflex Function", size="8", margin_bottom="1em"),
                rx.text("Ingrese f(x):", as_="label", font_size="large", margin_bottom="0.2em"),
                rx.input(
                    id="funcion_input",
                    value=State.funcion_str,
                    placeholder="Ej: (x**2 - 1) / (x - 1)",
                    on_change=State.set_funcion_str,
                    width="100%",
                    size="3",
                ),
                rx.text("Ingrese x:", as_="label", font_size="large", margin_top="1em", margin_bottom="0.2em"),
                rx.input(
                    id="punto_input",
                    value=State.punto_x_str,
                    placeholder="Ej: 1",
                    on_change=State.set_punto_x_str,
                    width="100%",
                    size="3",
                ),
                rx.button(
                    "Analizar",
                    on_click=State.analizar_funcion_event,
                    size="4",
                    width="100%",
                    margin_top="1em",
                ),
                rx.cond(
                    State.resultado_analisis,
                    rx.box(
                        rx.markdown("Resultado del Análisis:"),
                        rx.markdown(State.resultado_analisis, unwrap="p"),
                        border="1px solid #444",
                        padding="1em",
                        border_radius="md",
                        width="100%",
                        background_color=rx.color("gray", 3),
                        margin_top="1em",
                        font_size="large"
                    )
                ),
                rx.cond(
                    State.funcion_redefinida_latex,
                    rx.box(
                        rx.markdown("Función Redefinida $g(x)$:"),
                        rx.center(
                            rx.markdown(f"$$ {State.funcion_redefinida_latex} $$")
                        ),
                        border="1px solid #444",
                        padding="1em",
                        border_radius="md",
                        width="100%",
                        background_color=rx.color("gray", 3),
                        margin_top="1em",
                    )
                ),
                spacing="4",
                align="stretch",
                width="100%",
                max_width="600px",
                padding="2em",
                border_radius="xl",
                box_shadow="lg",
                background_color=rx.color("gray", 2),
            ),
            min_height="100vh",
            padding_x="1em",
            bg=rx.color("gray", 1),
        )
    )

app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="green",
        radius="large"
    )
)

app.add_page(index, title="Reflex Function")
