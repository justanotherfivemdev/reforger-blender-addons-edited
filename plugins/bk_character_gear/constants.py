# Arma Reforger character skeleton bones (Enfusion engine / SampleMod_NewCharacter)
CHARACTER_SKELETON_BONES = [
    "Root", "Pelvis",
    "Spine", "Spine1", "Spine2",
    "Neck", "Neck1", "Head",
    "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
    "RightShoulder", "RightArm", "RightForeArm", "RightHand",
    # Fingers L
    "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3",
    "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3",
    "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3",
    "LeftHandRing1", "LeftHandRing2", "LeftHandRing3",
    "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3",
    # Fingers R
    "RightHandThumb1", "RightHandThumb2", "RightHandThumb3",
    "RightHandIndex1", "RightHandIndex2", "RightHandIndex3",
    "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3",
    "RightHandRing1", "RightHandRing2", "RightHandRing3",
    "RightHandPinky1", "RightHandPinky2", "RightHandPinky3",
    # Legs
    "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
    "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase",
]

# Gear type enum items for UI
GEAR_TYPE_ITEMS = [
    ('HEADGEAR',  "Headgear",   "Helmets, hats, balaclavas - binds to Head bone"),
    ('VEST',      "Vest",       "Vests, plate carriers, chest rigs - binds to Spine/Spine1/Spine2"),
    ('BACKPACK',  "Backpack",   "Backpacks, packs - binds to Spine2"),
    ('GLOVES',    "Gloves",     "Gloves, hand gear - binds to hand/finger bones"),
    ('PANTS',     "Pants",      "Pants, leg gear - binds to leg bones"),
    ('BOOTS',     "Boots",      "Boots, footwear - binds to foot bones"),
    ('FULL_BODY', "Full Body",  "Full uniform - binds to full skeleton"),
    ('ACCESSORY', "Accessory",  "Patches, goggles, accessories - single bone binding"),
]

# Mapping of gear type to which bones are relevant
GEAR_BONE_MAPPING = {
    'HEADGEAR':  ["Head", "Neck", "Neck1"],
    'VEST':      ["Spine", "Spine1", "Spine2", "LeftShoulder", "RightShoulder"],
    'BACKPACK':  ["Spine1", "Spine2"],
    'GLOVES':    [b for b in CHARACTER_SKELETON_BONES if "Hand" in b or "Finger" in b],
    'PANTS':     [b for b in CHARACTER_SKELETON_BONES if any(x in b for x in ["UpLeg", "Leg", "Pelvis"])],
    'BOOTS':     [b for b in CHARACTER_SKELETON_BONES if any(x in b for x in ["Foot", "Toe", "Leg"])],
    'FULL_BODY': CHARACTER_SKELETON_BONES,
    'ACCESSORY': [],  # User picks the bone
}

# Default LOD ratios for gear (less aggressive than vehicles — gear is seen close-up)
GEAR_LOD_RATIOS = [0.5, 0.25, 0.12]
