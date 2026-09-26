# Four-toolhead configuration system

Three layers of configuration, so geometry never changes when materials or colours do:

1. **Roles (in each product):** `tool_roles` says what each tool does in that product (e.g. tool 4 = "horns" on the
   keyring, "TPU contact pads" on the phone stand). `requirements` can demand a material property:
   `{"tool_4": {"flexible": true, "strict": true, "preferred_material": "TPU"}}`.
2. **Loaded machine (`config/toolheads.json`):** what material/colour is physically in each tool now.
3. **Colour variant (`config/variants.json`):** recolours tools for a product run without touching geometry.

`cad/core/tools.py::effective_tools(product, variant)` merges them:

- colour from the variant (or the loaded colour), material from the loaded machine;
- a strict requirement that the loaded material violates -> **SETUP** issue (and costs use the preferred material);
- a non-strict one -> **WARN**;
- a functional flexible tool keeps its loaded colour (variants only recolour decoration).

Palette (`config/colors.json`): generic names, hex preview values, suggested tool, contrast partners, and
PLA/PETG/TPU availability. Materials (`config/materials.json`): density, temperatures, effective flow, flexibility
and a bonding matrix (good / fair / poor) used by validation for fused interfaces.

## Where the four tools earn their keep in the prototypes

| Product | What would otherwise need painting / assembly / other processes |
|---|---|
| CRW-001 keyring | 7 painted regions per side, both sides |
| CRW-002 magnet | painted face + printed/label banner; lettering is a knock-out (free) |
| CRW-003 mini | ~10 painted regions on a curved figure |
| CRW-004 stand | glued rubber feet/pads + painted artwork |
| CRW-005 articulated | painted skins + a separately made flexible tail, assembly of 5 parts |

## Tool-change budget (why the designs look the way they do)

Tool changes cost time (8 s assumed) and purge (0.06 g assumed) per change. The design rule is to put colour where
it costs few layers:

- **Sandwich inlays** (flat products): colour in the outer 3 layers of each face, single-tool core.
  Keyring: 18 changes total; magnet: 15; phone stand: 28 over 320 layers; articulated cow: 42 over 90 layers.
- **Vertical zoning** (3D figure): plinth layers are tool 4 only, patches sit high on the back, nostrils are
  dimples. The mini still needs ~199 changes - which is why it is batch-printed (24/plate -> ~0.5 g purge/unit).

`previews/<product>/tool-layers.png` shows the per-layer tool map for each product.
