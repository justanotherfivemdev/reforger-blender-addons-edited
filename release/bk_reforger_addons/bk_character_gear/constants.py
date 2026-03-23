# =============================================================================
# Arma Reforger character skeleton — Enfusion engine, October 2024 update
#
# Skeleton history:
#   v1  (legacy):  163 bones  — body + basic head
#   v220 (current): 220 bones — body (163) + full facial rig (57 new bones)
#
# Reference: https://reforger.armaplatform.com/news/modding-update-october-15-2024
# All gear should be tested against the 220-bone skeleton.
# Gear skinned to OLD head-hierarchy bones must be migrated to the Head bone.
# =============================================================================

# ── Body skeleton — 163 bones ─────────────────────────────────────────────────
_BODY_BONES = [
    # Root / Pelvis (2)
    "Root", "Pelvis",

    # Spine chain (5)
    "Spine", "Spine1", "Spine2", "Spine3", "Spine4",

    # Spine / torso helpers (8)
    "SpineBase", "CenterOfMass", "PelvisHelper",
    "HipsTwist_L", "HipsTwist_R",
    "SpineLower_Twist", "SpineMid_Twist", "SpineUpper_Twist",

    # Chest (2)
    "Chest", "ChestUpper",

    # Neck / Head (5)
    "Neck", "Neck1", "Neck2", "Head", "HeadEnd",

    # Neck / shoulder helpers (4)
    "NeckMuscle_L", "NeckMuscle_R", "Scapula_L", "Scapula_R",

    # Left arm — clavicle + deform chain + twist helpers (10)
    "LeftShoulder",
    "LeftArm", "LeftArmRoll", "LeftArmRoll1", "LeftArmRoll2",
    "LeftForeArm", "LeftForeArmRoll", "LeftForeArmRoll1",
    "LeftHand", "LeftHandHelper",

    # Left fingers — Thumb (no metacarpal): 3 phalanges + tip = 4
    #               Index / Middle / Ring / Pinky: metacarpal + 3 phalanges + tip = 5 each
    "LeftHandThumb1",  "LeftHandThumb2",  "LeftHandThumb3",  "LeftHandThumbEnd",
    "LeftHandIndex0",  "LeftHandIndex1",  "LeftHandIndex2",  "LeftHandIndex3",  "LeftHandIndexEnd",
    "LeftHandMiddle0", "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3", "LeftHandMiddleEnd",
    "LeftHandRing0",   "LeftHandRing1",   "LeftHandRing2",   "LeftHandRing3",   "LeftHandRingEnd",
    "LeftHandPinky0",  "LeftHandPinky1",  "LeftHandPinky2",  "LeftHandPinky3",  "LeftHandPinkyEnd",

    # Right arm — clavicle + deform chain + twist helpers (10)
    "RightShoulder",
    "RightArm", "RightArmRoll", "RightArmRoll1", "RightArmRoll2",
    "RightForeArm", "RightForeArmRoll", "RightForeArmRoll1",
    "RightHand", "RightHandHelper",

    # Right fingers (same structure as left)
    "RightHandThumb1",  "RightHandThumb2",  "RightHandThumb3",  "RightHandThumbEnd",
    "RightHandIndex0",  "RightHandIndex1",  "RightHandIndex2",  "RightHandIndex3",  "RightHandIndexEnd",
    "RightHandMiddle0", "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3", "RightHandMiddleEnd",
    "RightHandRing0",   "RightHandRing1",   "RightHandRing2",   "RightHandRing3",   "RightHandRingEnd",
    "RightHandPinky0",  "RightHandPinky1",  "RightHandPinky2",  "RightHandPinky3",  "RightHandPinkyEnd",

    # Left leg — deform chain + twist helpers (10)
    "LeftUpLeg", "LeftUpLegRoll", "LeftUpLegRoll1", "LeftUpLegRoll2",
    "LeftLeg", "LeftLegRoll", "LeftLegRoll1",
    "LeftFoot", "LeftToeBase", "LeftToeEnd",

    # Right leg — deform chain + twist helpers (10)
    "RightUpLeg", "RightUpLegRoll", "RightUpLegRoll1", "RightUpLegRoll2",
    "RightLeg", "RightLegRoll", "RightLegRoll1",
    "RightFoot", "RightToeBase", "RightToeEnd",

    # Equipment attachment / memory points (27)
    "WeaponHold_R", "WeaponHold_L",
    "WeaponCarry_B", "WeaponCarry_L", "WeaponCarry_R",
    "PropAttach_R", "PropAttach_L",
    "BackpackAttach", "BackpackAttach_L", "BackpackAttach_R",
    "HelmetAttach", "NeckAttach",
    "ChestAttach_L", "ChestAttach_R",
    "BeltAttach_L", "BeltAttach_R",
    "ThighAttach_L", "ThighAttach_R",
    "WristAttach_L", "WristAttach_R",
    "VestAttach",
    "PouchAttach_L", "PouchAttach_R",
    "ShoulderAttach_L", "ShoulderAttach_R",
    "BootAttach_L", "BootAttach_R",

    # IK targets and pole vectors (12)
    "IK_Foot_Root", "IK_Foot_L", "IK_Foot_R",
    "IK_Hand_Root", "IK_Hand_L", "IK_Hand_R",
    "IK_Prop_L", "IK_Prop_R",
    "Pole_Knee_L", "Pole_Knee_R",
    "Pole_Elbow_L", "Pole_Elbow_R",

    # Cloth / soft-body proxy (10)
    "Jacket_Front_L", "Jacket_Front_R",
    "Jacket_Back_L",  "Jacket_Back_R",
    "Belt_Front", "Belt_Back",
    "Backpack_Strap_L", "Backpack_Strap_R",
    "Breast_L", "Breast_R",
]

# ── Facial rig — 57 NEW bones added in the October 2024 skeleton update ────────
# These bones are children of the Head bone. All gear (helmets, chin straps, etc.)
# that was previously skinned to head-hierarchy bones MUST be re-skinned to the
# Head bone (or the appropriate body bone), per BI's official recommendation.
# Use the "Migrate Facial Weights" operator to automate this.
FACIAL_BONES = [
    "FaceRoot",

    # Jaw / mouth
    "Jaw", "JawEnd",

    # Tongue
    "TongueRoot", "Tongue", "Tongue1", "Tongue2", "TongueEnd",

    # Eyes
    "Eye_L", "EyeAim_L", "Eye_R", "EyeAim_R",

    # Eyelids — three segments each (inner / mid / outer)
    "EyeLid_Upper_L", "EyeLid_Upper_L_Inner", "EyeLid_Upper_L_Outer",
    "EyeLid_Lower_L", "EyeLid_Lower_L_Inner", "EyeLid_Lower_L_Outer",
    "EyeLid_Upper_R", "EyeLid_Upper_R_Inner", "EyeLid_Upper_R_Outer",
    "EyeLid_Lower_R", "EyeLid_Lower_R_Inner", "EyeLid_Lower_R_Outer",

    # Brows
    "Brow_Inner_L", "Brow_Mid_L", "Brow_Outer_L",
    "Brow_Inner_R", "Brow_Mid_R", "Brow_Outer_R",

    # Cheeks
    "Cheek_L", "Cheek_Puff_L", "Cheek_R", "Cheek_Puff_R",

    # Nose
    "NoseBridge", "NoseTip", "Nostril_L", "Nostril_R",

    # Lips
    "LipCorner_L", "LipCorner_R",
    "Lip_Upper_L", "Lip_Upper_Mid", "Lip_Upper_R",
    "Lip_Lower_L", "Lip_Lower_Mid", "Lip_Lower_R",
    "LipSeal_Upper", "LipSeal_Lower",

    # Teeth
    "Teeth_Upper", "Teeth_Lower",

    # Other facial features
    "Chin",
    "Ear_L", "Ear_R",
    "Forehead",

    # Head helper / neck-skin connection
    "HeadNod", "HeadNod_End", "NeckSkin_Front",
]

# ── Full 220-bone skeleton (body + facial) ─────────────────────────────────────
CHARACTER_SKELETON_BONES = _BODY_BONES + FACIAL_BONES
assert len(CHARACTER_SKELETON_BONES) == 220, (
    f"Expected 220 bones but got {len(CHARACTER_SKELETON_BONES)} — "
    "check _BODY_BONES and FACIAL_BONES for duplicates or missing entries"
)
# len(CHARACTER_SKELETON_BONES) == 220  (163 body + 57 facial)

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
# Per the BI Oct 2024 update: gear must NOT be skinned to facial bones.
# Even headgear / chin straps must use the 'Head' bone as a safe anchor.
GEAR_BONE_MAPPING = {
    # Strict binding to Head bone only.
    # Facial-bone skinning (e.g. chin strap to Jaw) breaks after the BI skeleton update.
    # Temporary fix for chin straps: skin to Head bone.
    'HEADGEAR': ["Head"],

    'VEST': [
        "Spine", "Spine1", "Spine2", "Spine3", "Spine4",
        "Chest", "ChestUpper",
        "LeftShoulder", "RightShoulder",
    ],

    'BACKPACK': [
        "Spine2", "Spine3", "Spine4",
        "BackpackAttach", "BackpackAttach_L", "BackpackAttach_R",
    ],

    'GLOVES': [b for b in _BODY_BONES if
               any(b.startswith(p) for p in (
                   "LeftHand", "RightHand", "LeftForeArm", "RightForeArm"
               )) and "Roll" not in b],

    'PANTS': [
        "Pelvis", "HipsTwist_L", "HipsTwist_R",
        "LeftUpLeg",  "LeftUpLegRoll",  "LeftUpLegRoll1",
        "RightUpLeg", "RightUpLegRoll", "RightUpLegRoll1",
        "LeftLeg",  "LeftLegRoll",
        "RightLeg", "RightLegRoll",
    ],

    'BOOTS': [
        "LeftLeg",   "LeftLegRoll",
        "RightLeg",  "RightLegRoll",
        "LeftFoot",  "LeftToeBase",  "LeftToeEnd",
        "RightFoot", "RightToeBase", "RightToeEnd",
    ],

    # Full body gear uses all body bones but NEVER facial bones.
    'FULL_BODY': _BODY_BONES,

    # User picks the binding bone manually via the Blender UI.
    'ACCESSORY': [],
}


# ── Default LOD ratios for gear ────────────────────────────────────────────────
# Less aggressive than vehicles; gear is seen close-up.
GEAR_LOD_RATIOS = [0.5, 0.25, 0.12]

# ── Character template reference ───────────────────────────────────────────────
# The official BI reference file distributed with SampleMod_NewCharacter.
# Users should browse for this file to enable template-based visualisation.
# Actual bone names MUST match the armature inside this file exactly.
CHARACTER_TEMPLATE_BLEND_NAME = "Character_Weights_Template.blend"

# Prefix used to tag all objects appended from the character template.
# Used to identify and remove them cleanly.
CHAR_TEMPLATE_PREFIX = "CHAR_TEMPLATE_"
