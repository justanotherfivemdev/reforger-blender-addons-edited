# =============================================================================
# Arma Reforger character skeleton — Enfusion engine
#
# Total: 224 bones — 113 body bones + 111 facial bones
#
# All gear should be tested against this skeleton.
# Gear skinned to facial bones must use the Head bone as a safe anchor.
# =============================================================================

# ── Body skeleton — 113 bones ─────────────────────────────────────────────────
_BODY_BONES = [
    # Root / Hips (2)
    "Root", "Hips",

    # Spine chain (5)
    "Spine1", "Spine2", "Spine3", "Spine4", "Spine5",

    # Neck / Head (4)
    "Neck1", "Neck2", "Neck3", "Head",

    # Pectorals / shoulder blades (4)
    "LeftPectoral", "RightPectoral",
    "LeftShoulderBlade", "RightShoulderBlade",

    # Right arm — clavicle + deform chain + twist helpers (6)
    "RightShoulder",
    "RightArm", "RightArmTwist",
    "RightForeArm", "RightForeArmTwist",
    "RightHand",

    # Right fingers — 5 bones each (Middle / Ring / Pinky / Index / Thumb) = 25
    "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3", "RightHandMiddle4", "RightHandMiddle5",
    "RightHandRing1",   "RightHandRing2",   "RightHandRing3",   "RightHandRing4",   "RightHandRing5",
    "RightHandPinky1",  "RightHandPinky2",  "RightHandPinky3",  "RightHandPinky4",  "RightHandPinky5",
    "RightHandIndex1",  "RightHandIndex2",  "RightHandIndex3",  "RightHandIndex4",  "RightHandIndex5",
    "RightHandThumb1",  "RightHandThumb2",  "RightHandThumb3",  "RightHandThumb4",  "RightHandThumb5",

    # Right hand extras (4)
    "RightHandInbetween", "RightHandProp",
    "RightHandUpperVolume", "RightHandLowerVolume",

    # Right arm volume / twist helpers (2)
    "RightForeArmVolume", "RightArmVolume",

    # Left arm — clavicle + deform chain + twist helpers (6)
    "LeftShoulder",
    "LeftArm", "LeftArmTwist",
    "LeftForeArm", "LeftForeArmTwist",
    "LeftHand",

    # Left hand extras (2)
    "LeftHandProp", "LeftHandInbetween",

    # Left fingers — 5 bones each (Middle / Ring / Pinky / Index / Thumb) = 25
    "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3", "LeftHandMiddle4", "LeftHandMiddle5",
    "LeftHandRing1",   "LeftHandRing2",   "LeftHandRing3",   "LeftHandRing4",   "LeftHandRing5",
    "LeftHandPinky1",  "LeftHandPinky2",  "LeftHandPinky3",  "LeftHandPinky4",  "LeftHandPinky5",
    "LeftHandIndex1",  "LeftHandIndex2",  "LeftHandIndex3",  "LeftHandIndex4",  "LeftHandIndex5",
    "LeftHandThumb1",  "LeftHandThumb2",  "LeftHandThumb3",  "LeftHandThumb4",  "LeftHandThumb5",

    # Left arm volume / twist helpers (4)
    "LeftHandUpperVolume", "LeftHandLowerVolume",
    "LeftForeArmVolume", "LeftArmVolume",

    # Stomach (3)
    "Stomach3", "Stomach2", "Stomach1",

    # Cloth / leg panels (4)
    "RightLegClothF", "LeftLegClothF",
    "RightLegClothB", "LeftLegClothB",

    # Right leg — deform chain + twist helpers + volume (6 deform + 2 volume)
    "RightLeg", "RightLegTwist",
    "RightKnee", "RightKneeTwist",
    "RightFoot", "RightToe",
    "RightKneeVolume", "RightLegVolume",

    # Left leg — deform chain + twist helpers + volume (6 deform + 2 volume)
    "LeftLeg", "LeftLegTwist",
    "LeftKnee", "LeftKneeTwist",
    "LeftFoot", "LeftToe",
    "LeftKneeVolume", "LeftLegVolume",

    # Collision proxy (1)
    "Collision",
]

# ── Facial rig — 111 bones ────────────────────────────────────────────────────
# These bones are children of the Head bone. All gear (helmets, chin straps, etc.)
# must NOT be skinned to facial bones — use the Head bone as the safe anchor.
FACIAL_BONES = [
    # Camera (1)
    "Camera",

    # General facial muscles (16)
    "BlowChick_left", "BlowChick_right",
    "CorrugatorSupercilii_left", "CorrugatorSupercilii_right",
    "DepressorAnguli_left", "DepressorAnguli_right",
    "DepressorSeptiNasil",
    "LeftFacialNoseCorner",
    "LevatorAnguli_left", "LevatorAnguli_right",
    "LevatorLabii_left", "LevatorLabii_right",
    "LevatorSuperioris_left", "LevatorSuperioris_right",
    "MassaterStretch_left", "MassaterStretch_right",

    # Jaw muscles / cheek (4)
    "Massater_left", "Massater_right",
    "Mentalis_left", "Mentalis_right",

    # Nose / forehead (6)
    "Nasalis_left", "Nasalis_right",
    "Occipitalis_left", "Occipitalis_right",
    "Occipitofrontalis_left", "Occipitofrontalis_right",

    # OrbicularisOculi — eye-ring muscles, bottom row (12)
    "OrbicularisOculi_bottomCenterLid_left",  "OrbicularisOculi_bottomCenterLid_right",
    "OrbicularisOculi_bottomCenter_left",     "OrbicularisOculi_bottomCenter_right",
    "OrbicularisOculi_bottomLeftLid_left",    "OrbicularisOculi_bottomLeftLid_right",
    "OrbicularisOculi_bottomLeft_left",       "OrbicularisOculi_bottomLeft_right",
    "OrbicularisOculi_bottomRightLid_left",   "OrbicularisOculi_bottomRightLid_right",
    "OrbicularisOculi_bottomRight_left",      "OrbicularisOculi_bottomRight_right",

    # OrbicularisOculi — corners / nostril (4)
    "OrbicularisOculi_cornerLeft_left",       "OrbicularisOculi_cornerLeft_right",
    "OrbicularisOculi_nostril_left",          "OrbicularisOculi_nostril_right",

    # OrbicularisOculi — upper row (12)
    "OrbicularisOculi_upperCenterLid_left",   "OrbicularisOculi_upperCenterLid_right",
    "OrbicularisOculi_upperCenter_left",      "OrbicularisOculi_upperCenter_right",
    "OrbicularisOculi_upperLeftLid_left",     "OrbicularisOculi_upperLeftLid_right",
    "OrbicularisOculi_upperLeft_left",        "OrbicularisOculi_upperLeft_right",
    "OrbicularisOculi_upperRightLid_left",    "OrbicularisOculi_upperRightLid_right",
    "OrbicularisOculi_upperRight_left",       "OrbicularisOculi_upperRight_right",

    # Orbicularis oris — lip-ring muscles (14)
    "Orbicularis_bottomCenter",
    "Orbicularis_bottomCenterLips",
    "Orbicularis_bottomLeft",
    "Orbicularis_bottomLipsLeft",
    "Orbicularis_bottomLipsRight",
    "Orbicularis_bottomRight",
    "Orbicularis_cornerLeft",
    "Orbicularis_cornerRight",
    "Orbicularis_upperCenter",
    "Orbicularis_upperCenterLips",
    "Orbicularis_upperLeft",
    "Orbicularis_upperLeftLips",
    "Orbicularis_upperRight",
    "Orbicularis_upperRightLips",

    # Other face / neck muscles (9)
    "Procerus",
    "Risorius_left", "Risorius_right",
    "Temporalis_back_left", "Temporalis_back_right",
    "Temporalis_front_left", "Temporalis_front_right",
    "ZygomaticusMajor_left", "ZygomaticusMajor_right",

    # Zygomaticus minor / platysma (4)
    "ZygomaticusMinor_left", "ZygomaticusMinor_right",
    "PlatysmaMinor_left", "PlatysmaMinor_right",

    # Jaw / mouth (4)
    "jawRP", "Jaw",
    "leftJawSpikeBone", "rightJawSpikeBone",

    # Tongue (6)
    "tongueRoot", "tongueMiddle", "tongueUpper",
    "tongueTip", "tongueLeftRoll", "tongueRightRoll",

    # Left eye + pupils (10)
    "leftEye", "EyeLeftPupil",
    "leftEye_pupil1", "leftEye_pupil2", "leftEye_pupil3", "leftEye_pupil4",
    "leftEye_pupil5", "leftEye_pupil6", "leftEye_pupil7", "leftEye_pupil8",

    # Right eye + pupils (9)
    "rightEye",
    "rightEye_pupil1", "rightEye_pupil2", "rightEye_pupil3", "rightEye_pupil4",
    "rightEye_pupil5", "rightEye_pupil6", "rightEye_pupil7", "rightEye_pupil8",
]

# ── Full 224-bone skeleton (body + facial) ─────────────────────────────────────
CHARACTER_SKELETON_BONES = _BODY_BONES + FACIAL_BONES
assert len(CHARACTER_SKELETON_BONES) == 224, (
    f"Expected 224 bones but got {len(CHARACTER_SKELETON_BONES)} — "
    "check _BODY_BONES and FACIAL_BONES for duplicates or missing entries"
)
# len(CHARACTER_SKELETON_BONES) == 224  (113 body + 111 facial)

# Quick-lookup sets
_BODY_BONE_SET = set(_BODY_BONES)
FACIAL_BONE_SET = set(FACIAL_BONES)
CHARACTER_SKELETON_BONE_SET = set(CHARACTER_SKELETON_BONES)

# Minimum weight value treated as non-zero for normalization and cleanup
WEIGHT_EPSILON = 1e-6


# ── Gear type enum items for UI ────────────────────────────────────────────────
GEAR_TYPE_ITEMS = [
    ('HEADGEAR',  "Headgear",   "Helmets, hats, balaclavas — binds to Head bone only"),
    ('VEST',      "Vest",       "Vests, plate carriers, chest rigs — binds to spine / shoulder bones"),
    ('BACKPACK',  "Backpack",   "Backpacks, packs — binds to upper-spine and backpack attachment bones"),
    ('GLOVES',    "Gloves",     "Gloves, hand gear — binds to hand / finger bones"),
    ('PANTS',     "Pants",      "Pants, leg gear — binds to pelvis and leg bones"),
    ('BOOTS',     "Boots",      "Boots, footwear — binds to lower-leg and foot bones"),
    ('FULL_BODY', "Full Body",  "Full uniform — binds to entire body skeleton (excluding facial bones)"),
    ('ACCESSORY', "Accessory",  "Patches, goggles, accessories — single bone binding (user selects)"),
]


# ── Gear type → relevant deformation bones ─────────────────────────────────────
# IMPORTANT: Facial bones are intentionally excluded from all mappings.
# Gear must NOT be skinned to facial bones.
# Even headgear / chin straps must use the 'Head' bone as a safe anchor.
GEAR_BONE_MAPPING = {
    # Strict binding to Head bone only.
    # Facial-bone skinning (e.g. chin strap to Jaw) is not supported.
    'HEADGEAR': ["Head"],

    'VEST': [
        "Spine1", "Spine2", "Spine3", "Spine4", "Spine5",
        "LeftShoulder", "RightShoulder",
        "LeftPectoral", "RightPectoral",
        "LeftShoulderBlade", "RightShoulderBlade",
    ],

    'BACKPACK': [
        "Spine3", "Spine4", "Spine5",
        "LeftShoulderBlade", "RightShoulderBlade",
    ],

    'GLOVES': [b for b in _BODY_BONES if
               any(b.startswith(p) for p in (
                   "LeftHand", "RightHand", "LeftForeArm", "RightForeArm"
               )) and "Volume" not in b],

    'PANTS': [
        "Hips",
        "Stomach1", "Stomach2", "Stomach3",
        "LeftLeg",  "LeftLegTwist",
        "RightLeg", "RightLegTwist",
    ],

    'BOOTS': [
        "LeftKnee",  "LeftKneeTwist",
        "RightKnee", "RightKneeTwist",
        "LeftFoot",  "LeftToe",
        "RightFoot", "RightToe",
    ],

    # Full body gear uses all body bones but NEVER facial bones.
    'FULL_BODY': _BODY_BONES,

    # User picks the binding bone manually via the Blender UI.
    'ACCESSORY': [],
}


# ── Default LOD ratios for gear ────────────────────────────────────────────────
# Less aggressive than vehicles; gear is seen close-up.
GEAR_LOD_RATIOS = [0.5, 0.25, 0.12]

# Shadow LOD — very low poly mesh used only for shadow rendering.
SHADOW_LOD_RATIO = 0.05

# View LOD — optional simplified version for extreme distances.
VIEW_LOD_RATIO = 0.10

# ── Character template reference ───────────────────────────────────────────────
# The official BI reference file distributed with SampleMod_NewCharacter.
# Users should browse for this file to enable template-based visualisation.
# Actual bone names MUST match the armature inside this file exactly.
CHARACTER_TEMPLATE_BLEND_NAME = "Character_Weights_Template.blend"

# Prefix used to tag all objects appended from the character template.
# Used to identify and remove them cleanly.
CHAR_TEMPLATE_PREFIX = "CHAR_TEMPLATE_"
