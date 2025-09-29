"""ATEM Models Configuration."""

# Configuration des inputs disponibles par modèle d'ATEM
ATEM_MODELS = {    
    "ATEM Mini Extreme ISO": {
        "inputs": {
            1: "input1",
            2: "input2",
            3: "input3",
            4: "input4",
            5: "input5",
            6: "input6",
            7: "input7",
            8: "input8",
            2001: "color1",
            2002: "color2",
            3010: "mediaPlayer1",
            3020: "mediaPlayer2",
            6000: "superSource",
            0: "black"
        },
        "max_inputs": 8,
        "has_streaming": True,
        "has_recording": True,
        "has_multiview": True,
        "has_iso_recording": True,
        "has_advanced_chroma": True
    },
    
   
    
    # Modèle par défaut pour les ATEM non reconnus
    "DEFAULT": {
        "inputs": {
            1: "input1",
            2: "input2",
            3: "input3",
            4: "input4",
            5: "input5",
            6: "input6",
            7: "input7",
            8: "input8",
            2001: "color1",
            2002: "color2",
            3010: "mediaPlayer1",
            3020: "mediaPlayer2",
            10010: "Program",
            10011: "Preview",
            0: "black"
        },
        "max_inputs": 8,
        "has_streaming": False,
        "has_recording": False,
        "has_multiview": False
    }
}


def get_model_config(model_name: str) -> dict:
    """Get configuration for a specific ATEM model."""
    # Cherche le modèle exact
    for key in ATEM_MODELS:
        if key.lower() in model_name.lower():
            return ATEM_MODELS[key]
    
    # Si pas trouvé, retourne la config par défaut
    return ATEM_MODELS["DEFAULT"]


def get_input_choices(model_name: str) -> dict:
    """Get available input choices for a specific ATEM model."""
    config = get_model_config(model_name)
    return config["inputs"]


def get_input_name(model_name: str, input_number: int) -> str:
    """Get the name of a specific input for a model."""
    config = get_model_config(model_name)
    return config["inputs"].get(input_number, f"Input {input_number}")