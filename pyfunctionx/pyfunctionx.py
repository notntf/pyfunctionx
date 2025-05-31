import reflex as rx
import sympy
from sympy import symbols, sympify, limit, oo, latex

# Símbolo principal para la variable x
x_sym = symbols('x')

# Configuración de MathJax para renderizado de ecuaciones matemáticas
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
    """Estado de la aplicación que maneja los datos y la lógica principal"""
    
    # Variables de estado
    funcion_str: str = "(x**2 - 1) / (x - 1)"  # Función ingresada por el usuario
    punto_x_str: str = ""  # Valor de x a evaluar
    resultado_analisis: str = ""  # Resultado del análisis de continuidad
    funcion_redefinida_latex: str = ""  # Función redefinida (si es aplicable)

    def limpiar_campos(self):
        """Restablece todos los campos a sus valores iniciales"""
        self.funcion_str = ""
        self.punto_x_str = ""
        self.resultado_analisis = ""
        self.funcion_redefinida_latex = ""

    def _parse_input(self, expr_str, val_str):
        """
        Convierte las entradas de texto en expresiones sympy válidas
        Args:
            expr_str: string con la función matemática
            val_str: string con el valor de x a evaluar
        Returns:
            tuple: (función sympy, punto evaluado, mensaje de error)
        """
        try:
            # Procesamiento de la función: conversión de sintaxis y manejo de raíces
            expr_str_sympy = expr_str.replace('^', '**').replace('ln(', 'log(')
            
            # Convertir notación sqrt[n](expr) a root(expr, n)
            import re
            expr_str_sympy = re.sub(r'sqrt\[([^\]]+)\]\(([^\)]+)\)', r'root(\2, \1)', expr_str_sympy)
            expr_str_sympy = expr_str_sympy.replace('sqrt(', 'root(, 2)').replace('root(, 2)', 'root(')
            
            func = sympify(expr_str_sympy)
        except (SyntaxError, TypeError, sympy.SympifyError) as e:
            return None, None, f"Error al parsear la función: {str(e)}"
            
        try:
            # Procesamiento del valor de x (admite infinito)
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
        """Analiza la continuidad de la función en el punto dado"""
        self.resultado_analisis = ""
        self.funcion_redefinida_latex = ""

        # Validación de entradas vacías
        if not self.funcion_str.strip() or not self.punto_x_str.strip():
            self.resultado_analisis = "Por favor, ingrese una función y un valor para x."
            return

        # Parseo de entradas
        func, punto_eval, error_msg = self._parse_input(self.funcion_str, self.punto_x_str)
        if error_msg:
            self.resultado_analisis = error_msg
            return
        if func is None or punto_eval is None:
            self.resultado_analisis = "Error interno al parsear la entrada."
            return

        # Cálculo de valores y límites
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

        # Análisis de continuidad
        f_a_definida = valor_en_punto.is_finite
        lim_existe_y_finito = lim_en_punto.is_finite
        
        # Preparación de strings para LaTeX
        punto_eval_latex = latex(punto_eval) 
        sub_general_str = f"x \\to {punto_eval_latex}"
        sub_izquierda_str = f"x \\to {punto_eval_latex}^-"
        sub_derecha_str = f"x \\to {punto_eval_latex}^+"

        # Función para formatear valores especiales (infinito, raíces complejas)
        def format_val(val):
            if val == oo:
                return r"\infty"
            elif val == -oo:
                return r"-\infty"
            elif isinstance(val, sympy.Pow) and val.args[0] == -1:
                return r"\text{Indefinido (complejo)}"
            return latex(val)

        # Construcción del mensaje de resultados
        mensaje = f"Análisis para $f(x) = {latex(func)}$ en $x = {punto_eval_latex}$:\n\n"
        
        if f_a_definida and lim_existe_y_finito and valor_en_punto == lim_en_punto:
            mensaje += f"✅ **La función es CONTINUA** en $x = {punto_eval_latex}$.\n\n"
            mensaje += f"- $f({punto_eval_latex}) = {format_val(valor_en_punto)}$\n"
            mensaje += f"- $\\lim_{{{sub_general_str}}} f(x) = {format_val(lim_en_punto)}$"
        else:
            mensaje += f"❌ **La función es DISCONTINUA** en $x = {punto_eval_latex}$.\n\n"
            mensaje += f"- Valor en el punto: $f({punto_eval_latex}) = {format_val(valor_en_punto)}$\n"
            mensaje += f"- Límite general: $\\lim_{{{sub_general_str}}} f(x) = {format_val(lim_en_punto)}$\n\n"

            # Clasificación del tipo de discontinuidad
            if lim_existe_y_finito:
                mensaje += "**Tipo:** Discontinuidad EVITABLE\n\n"
                f_redefinida = sympy.Piecewise((lim_en_punto, sympy.Eq(x_sym, punto_eval)), (func, True))
                # Versión con cases (más legible)
                self.funcion_redefinida_latex = (
                    r"\begin{cases} " +
                    latex(lim_en_punto) + r" & \text{si } x = " + latex(punto_eval) + r" \\ " +
                    latex(func) + r" & \text{si } x \neq " + latex(punto_eval) +
                    r"\end{cases}"
                )
            else:
                if lim_izquierda.is_finite and lim_derecha.is_finite and lim_izquierda != lim_derecha:
                    mensaje += "**Tipo:** Discontinuidad NO EVITABLE (de salto finito)"
                elif abs(lim_en_punto) == oo or abs(lim_izquierda) == oo or abs(lim_derecha) == oo:
                    mensaje += "**Tipo:** Discontinuidad NO EVITABLE (infinita)"
                else:
                    mensaje += "**Tipo:** Discontinuidad NO EVITABLE (esencial)"

        self.resultado_analisis = mensaje

def index() -> rx.Component:
    """Componente principal de la interfaz de usuario"""
    return rx.fragment(
        rx.html(MATHJAX_SCRIPT_HTML),
        rx.center(
            rx.vstack(
                # Título principal
                rx.heading("Reflex Function", size="8", margin="0"),
                rx.text("Evaluador de Límites de funciones", size="4", margin_bottom="20px"),
                
                # Sección de entrada de función
                rx.text("Ingrese f(x):", as_="label", font_size="large", margin_bottom="0.2em"),
                
                # Botones para símbolos matemáticos
                rx.hstack(
                    *[
                        rx.button(
                            symbol,
                            on_click=lambda s=symbol: State.set_funcion_str(State.funcion_str + s),
                            size="2",
                        )
                        for symbol in ["x", "^", "(", ")", "/", "*", "+", "-",
                                    "sqrt[](", "root(", "sin(", "cos(", "tan(", "log(", "ln("]
                    ],
                    wrap="wrap",
                    spacing="2",
                    width="100%",
                ),
                rx.text("Nota: Para raíces use sqrt[n](expr) o root(expr, n)", 
                       font_size="small", color=rx.color("gray", 10)),
                
                # Campo de entrada para la función
                rx.input(
                    id="funcion_input",
                    value=State.funcion_str,
                    placeholder="Ej: (x^2 - 1)/(x - 1)",
                    on_change=State.set_funcion_str,
                    width="100%",
                    size="3",
                ),
                
                # Sección de entrada para el valor de x
                rx.text("Ingrese el valor de x a evaluar:", 
                       as_="label", font_size="large", margin_top="1em", margin_bottom="0.2em"),
                rx.input(
                    id="punto_input",
                    value=State.punto_x_str,
                    placeholder="Ej: 1, 2.5, oo (infinito), -oo",
                    on_change=State.set_punto_x_str,
                    width="100%",
                    size="3",
                ),

                # Botones de acción (Analizar y Limpiar)
                rx.hstack(
                    rx.button(
                        "Analizar",
                        on_click=State.analizar_funcion_event,
                        size="4",
                        flex="1",
                        color_scheme="green",
                    ),
                    rx.button(
                        "Limpiar",
                        on_click=State.limpiar_campos,
                        size="4",
                        flex="1",
                        color_scheme="gray",
                        variant="soft",
                    ),
                    spacing="4",
                    width="100%",
                    margin_top="1em",
                ),

                # Sección de resultados
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
                
                # Sección de función redefinida (si aplica)
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
                
                # Estilos del contenedor principal
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

# Configuración de la aplicación
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="green",
        radius="large"
    )
)

# Añadir la página principal
app.add_page(index, title="Reflex Function")