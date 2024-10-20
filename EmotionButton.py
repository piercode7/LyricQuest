import tkinter as tk


def lighten_color(color, factor=0.7):
    # Converte un colore esadecimale in RGB
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    # Converte un colore RGB in esadecimale
    def rgb_to_hex(rgb_color):
        return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

    rgb = hex_to_rgb(color)
    # Applica il fattore di schiarimento
    lighter_rgb = tuple(min(int(c + (255 - c) * factor), 255) for c in rgb)
    return rgb_to_hex(lighter_rgb)


# Definisci una mappa dei colori per le emozioni
base_color_map = {
    'anger': '#ff0000',  # Rosso
    'disgust': '#008000',  # Verde
    'fear': '#800080',  # Viola
    'joy': '#ffff00',  # Giallo
    'neutral': '#505050',  # Grigio
    'sadness': '#0000ff',  # Blu
    'surprise': '#ffa500'  # Arancione
}

# Applica la schiaritura ai colori della mappa
color_map = {emotion: lighten_color(color) for emotion, color in base_color_map.items()}


# classe per costruire i bottoni cliccabili nella schermata in basso per filtrare i sentimenti negli elenchi
class EmotionButton(tk.Button):
    def __init__(self, master=None, emotion=None, search_func=None, output_widget=None, **kwargs):
        super().__init__(master, **kwargs)
        self.emotion = emotion
        self.search_func = search_func
        self.output_widget = output_widget
        self.pressed = False
        self.config(command=self.toggle)
        self.default_color = self.cget('bg')  # Salva il colore di sfondo predefinito

    def toggle(self):
        self.pressed = not self.pressed
        if self.pressed:
            self.configure(relief=tk.SUNKEN, bg=color_map.get(self.emotion, 'light gray'))
        else:
            self.configure(relief=tk.RAISED, bg=self.default_color)
        if self.search_func:
            self.search_func(self.output_widget)
