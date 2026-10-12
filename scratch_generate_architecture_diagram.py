import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Set up clean academic typography
plt.rcParams['font.family'] = 'serif'
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['font.size'] = 10

def draw_pcg_waveform(ax, x0, y0, w, h):
    """Draw a clean stylized PCG audio wave with S1 and S2 bursts."""
    t = np.linspace(0, 4*np.pi, 250)
    # S1 burst around pi, S2 burst around 3pi
    s1 = np.exp(-((t - np.pi)/0.35)**2) * np.sin(28*t)
    s2 = 0.65 * np.exp(-((t - 2.8*np.pi)/0.3)**2) * np.sin(32*t)
    # murmur between S1 and S2
    murmur = 0.25 * np.exp(-((t - 1.9*np.pi)/0.9)**2) * np.sin(45*t) * (np.random.RandomState(42).randn(len(t))*0.3 + 1.0)
    wave = s1 + s2 + murmur
    wave = wave / np.max(np.abs(wave)) # normalize to [-1, 1]

    # Map to coordinates
    xs = x0 + (t / (4*np.pi)) * w
    ys = y0 + h/2 + wave * (h * 0.42)
    ax.plot(xs, ys, color='black', lw=0.85)

def draw_ecg_waveform(ax, x0, y0, w, h):
    """Draw a clean stylized 2-beat ECG trace with P-Q-R-S-T morphology."""
    t = np.linspace(0, 2, 400)
    def single_ecg(phase):
        val = np.zeros_like(phase)
        # P wave
        val += 0.20 * np.exp(-((phase - 0.20)/0.045)**2)
        # Q dip
        val -= 0.18 * np.exp(-((phase - 0.32)/0.02)**2)
        # R peak
        val += 1.00 * np.exp(-((phase - 0.36)/0.025)**2)
        # S dip
        val -= 0.35 * np.exp(-((phase - 0.40)/0.02)**2)
        # T wave
        val += 0.32 * np.exp(-((phase - 0.58)/0.07)**2)
        return val

    beat1 = single_ecg(t % 1.0)
    xs = x0 + (t / 2.0) * w
    ys = y0 + h/2 + (beat1 - 0.15) * (h * 0.42)
    ax.plot(xs, ys, color='black', lw=0.9)

def draw_echo_frames(ax, x0, y0, w, h):
    """Draw stylized End-Diastole and End-Systole cardiac ultrasound frame icons."""
    # Two small adjacent monitor boxes
    box_w = (w - 2) / 2
    # Frame 1: ED (Large LV chamber)
    f1 = patches.Rectangle((x0, y0), box_w, h, facecolor='#f8f8f8', edgecolor='black', lw=0.8)
    ax.add_patch(f1)
    # Cardiac wedge / sector outline
    ax.plot([x0 + box_w*0.5, x0 + 1.2], [y0 + h - 1.2, y0 + 1.5], color='#777777', lw=0.6, ls=':')
    ax.plot([x0 + box_w*0.5, x0 + box_w - 1.2], [y0 + h - 1.2, y0 + 1.5], color='#777777', lw=0.6, ls=':')
    # Large chamber ellipse
    e1 = patches.Ellipse((x0 + box_w*0.5, y0 + h*0.42), box_w*0.62, h*0.55,
                         facecolor='#e2e2e2', edgecolor='black', lw=0.8)
    ax.add_patch(e1)
    ax.text(x0 + box_w*0.5, y0 + h - 2.8, "ED Frame", fontsize=7.0, ha='center', fontweight='bold')

    # Frame 2: ES (Contracted small LV chamber)
    x1 = x0 + box_w + 2
    f2 = patches.Rectangle((x1, y0), box_w, h, facecolor='#f8f8f8', edgecolor='black', lw=0.8)
    ax.add_patch(f2)
    ax.plot([x1 + box_w*0.5, x1 + 1.2], [y1 if 'y1' in locals() else y0 + h - 1.2, y0 + 1.5], color='#777777', lw=0.6, ls=':')
    ax.plot([x1 + box_w*0.5, x1 + box_w - 1.2], [y0 + h - 1.2, y0 + 1.5], color='#777777', lw=0.6, ls=':')
    # Smaller contracted chamber ellipse
    e2 = patches.Ellipse((x1 + box_w*0.5, y0 + h*0.42), box_w*0.38, h*0.35,
                         facecolor='#cccccc', edgecolor='black', lw=0.8)
    ax.add_patch(e2)
    ax.text(x1 + box_w*0.5, y0 + h - 2.8, "ES Frame", fontsize=7.0, ha='center', fontweight='bold')

def generate_improved_diagram():
    fig, ax = plt.subplots(figsize=(15, 8.8), dpi=300)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 96)
    ax.axis('off')

    c_white = '#ffffff'
    c_lightgray = '#f5f5f5'
    c_midgray = '#e8e8e8'
    c_darkgray = '#444444'
    c_black = '#000000'

    # Client specifications
    clients = [
        {
            'tier': 'Hospital A: Rural Clinic (Tier 1)',
            'modality': 'Phonocardiogram (PCG Audio)',
            'dataset': 'CirCor DigiScope (11,162 Segments)',
            'tensor': r'$\mathbf{x}^A \in \mathbb{R}^{1 \times 64 \times 157}$',
            'desc': 'Log-Mel Spectrogram (64 bins)',
            'encoder_name': 'PCGNet (2D CNN)',
            'encoder_arch': '3 Conv Blocks + AdaptPool\n(355,426 Params)',
            'draw_func': draw_pcg_waveform,
            'yo': 66
        },
        {
            'tier': 'Hospital B: District General Hospital (Tier 2)',
            'modality': 'Electrocardiogram (ECG 9-Lead)',
            'dataset': 'ZZU-pECG (14,190 Recordings)',
            'tensor': r'$\mathbf{x}^B \in \mathbb{R}^{9 \times 5000}$',
            'desc': '10-sec 500 Hz Multi-Lead',
            'encoder_name': 'ECGResNet (1D ResNet)',
            'encoder_arch': 'Stem + 5 ResBlocks + 1D GAP\n(1,970,978 Params)',
            'draw_func': draw_ecg_waveform,
            'yo': 36.5
        },
        {
            'tier': 'Hospital C: Tertiary Children\'s Heart Centre (Tier 3)',
            'modality': 'Echocardiogram (Echo Ultrasound)',
            'dataset': 'EchoNet-Pediatric (3,258 Frame Pairs)',
            'tensor': r'$\mathbf{x}^C \in \mathbb{R}^{2 \times 112 \times 112}$',
            'desc': 'Dual-Frame (ED & ES Stacked)',
            'encoder_name': 'EchoNet (4-Block CNN)',
            'encoder_arch': '4 Conv Blocks + 2D GAP\n(422,178 Params)',
            'draw_func': draw_echo_frames,
            'yo': 7
        }
    ]

    for cl in clients:
        yo = cl['yo']

        # Outer Client Container Box
        client_box = patches.FancyBboxPatch((2, yo), 89, 26,
                                           boxstyle="round,pad=0.4",
                                           facecolor=c_white, edgecolor=c_black,
                                           linewidth=1.2, linestyle='--')
        ax.add_patch(client_box)

        # Hospital Header
        ax.text(4, yo + 24.2, cl['tier'], fontsize=10.2, fontweight='bold', va='top')
        ax.text(4, yo + 22.0, f"{cl['modality']} — {cl['dataset']}", fontsize=8.5, fontstyle='italic', color=c_darkgray, va='top')

        # ------------------------------------------------------------------
        # Column 1: Input Representation Box (x=4 to 22, width=18)
        # ------------------------------------------------------------------
        in_box = patches.FancyBboxPatch((4, yo + 1.8), 18, 17.5,
                                        boxstyle="square,pad=0.2",
                                        facecolor=c_lightgray, edgecolor=c_black, linewidth=1.0)
        ax.add_patch(in_box)
        ax.text(13, yo + 18.2, "Clinical Input Data", fontsize=8.5, fontweight='bold', ha='center', va='top')
        ax.text(13, yo + 16.2, cl['tensor'], fontsize=8.2, ha='center', va='top')
        ax.text(13, yo + 14.3, cl['desc'], fontsize=7.2, ha='center', va='top', color=c_darkgray)

        # Draw waveform / icon inside lower half of input box
        cl['draw_func'](ax, 5.5, yo + 3.0, 15, 8.5)

        # Arrow: Input -> Encoder
        ax.annotate('', xy=(24.5, yo + 10.5), xytext=(22.0, yo + 10.5),
                    arrowprops=dict(facecolor=c_black, edgecolor=c_black, width=1.0, headwidth=4.5, headlength=4.5))

        # ------------------------------------------------------------------
        # Column 2: Modality-Specific Feature Encoder (x=24.5 to 44.5, width=20)
        # ------------------------------------------------------------------
        enc_box = patches.FancyBboxPatch((24.5, yo + 1.8), 20, 17.5,
                                         boxstyle="square,pad=0.2",
                                         facecolor=c_lightgray, edgecolor=c_black, linewidth=1.2)
        ax.add_patch(enc_box)
        ax.text(34.5, yo + 17.5, cl['encoder_name'], fontsize=9.2, fontweight='bold', ha='center', va='top')
        ax.text(34.5, yo + 14.5, "Modality Feature Extractor", fontsize=7.6, fontstyle='italic', ha='center', va='top', color=c_darkgray)
        ax.text(34.5, yo + 11.5, cl['encoder_arch'], fontsize=7.6, ha='center', va='top')
        ax.text(34.5, yo + 4.5, r'$f_k(\mathbf{x}_i^k; \theta_k) \rightarrow \mathbf{e}_i^k$', fontsize=8.5, ha='center', va='top')

        # Arrow: Encoder -> Embedding Junction
        ax.annotate('', xy=(47.5, yo + 10.5), xytext=(44.5, yo + 10.5),
                    arrowprops=dict(facecolor=c_black, edgecolor=c_black, width=1.0, headwidth=4.5, headlength=4.5))

        # Latent vector tag box
        emb_box = patches.FancyBboxPatch((47.5, yo + 7.5), 9, 6.0,
                                         boxstyle="round,pad=0.2",
                                         facecolor=c_white, edgecolor=c_black, linewidth=1.0)
        ax.add_patch(emb_box)
        ax.text(52, yo + 12.0, "Latent\nVector", fontsize=7.0, ha='center', va='top')
        ax.text(52, yo + 8.8, r'$\mathbf{e}_i^k \in \mathbb{R}^{128}$', fontsize=7.8, fontweight='bold', ha='center', va='top')

        # ------------------------------------------------------------------
        # Branching from Embedding Vector:
        # Branch A (Up): Local Classifier Head h_k
        # Branch B (Down): Projection Head g_k
        # ------------------------------------------------------------------
        # Branch A: Arrow up-right to Classifier
        ax.annotate('', xy=(60, yo + 15.5), xytext=(56.5, yo + 11.0),
                    arrowprops=dict(arrowstyle="->", color=c_black, lw=1.1))

        # Classifier Box
        clf_box = patches.FancyBboxPatch((60, yo + 12.0), 16, 7.5,
                                         boxstyle="square,pad=0.2",
                                         facecolor=c_white, edgecolor=c_black, linewidth=1.0)
        ax.add_patch(clf_box)
        ax.text(68, yo + 18.2, "Classifier " + r'$h_k(\cdot; \phi_k)$', fontsize=8.2, fontweight='bold', ha='center', va='top')
        ax.text(68, yo + 15.8, r'Linear($128 \rightarrow 2$)', fontsize=7.4, ha='center', va='top')
        ax.text(68, yo + 13.5, r'Logits $\hat{y}_i \in \{0, 1\} \Rightarrow \mathcal{L}_{\mathrm{CE}}^k$', fontsize=7.6, ha='center', va='top')

        # Branch B: Arrow down-right to Projection Head
        ax.annotate('', xy=(60, yo + 5.5), xytext=(56.5, yo + 9.5),
                    arrowprops=dict(arrowstyle="->", color=c_black, lw=1.1))

        # Projection Head Box
        proj_box = patches.FancyBboxPatch((60, yo + 1.8), 16, 8.0,
                                          boxstyle="square,pad=0.2",
                                          facecolor=c_lightgray, edgecolor=c_black, linewidth=1.2)
        ax.add_patch(proj_box)
        ax.text(68, yo + 8.8, "Projection Head " + r'$g_k$', fontsize=8.2, fontweight='bold', ha='center', va='top')
        ax.text(68, yo + 6.6, r'$\mathbb{R}^{128} \rightarrow \mathbb{R}^{64}$ (8,256 Params)', fontsize=7.4, ha='center', va='top')
        ax.text(68, yo + 4.4, r'LayerNorm + L2 $\rightarrow \mathbb{S}^{63}$', fontsize=7.4, ha='center', va='top')

        # Arrow: Projection Head -> Prototypes Box
        ax.annotate('', xy=(78.5, yo + 5.8), xytext=(76.0, yo + 5.8),
                    arrowprops=dict(facecolor=c_black, edgecolor=c_black, width=1.0, headwidth=4.5, headlength=4.5))

        # ------------------------------------------------------------------
        # Column 3: Local Class Prototypes Box (x=78.5 to 89.5, width=11)
        # ------------------------------------------------------------------
        proto_box = patches.FancyBboxPatch((78.5, yo + 1.8), 11.5, 17.5,
                                           boxstyle="square,pad=0.2",
                                           facecolor=c_white, edgecolor=c_black, linewidth=1.0)
        ax.add_patch(proto_box)
        ax.text(84.25, yo + 18.0, "Local Class\nPrototypes", fontsize=8.0, fontweight='bold', ha='center', va='top')
        ax.text(84.25, yo + 13.5, r'$\bar{\mathbf{z}}_i^k \in \mathbb{S}^{63}$' + '\nUnit Vector', fontsize=7.2, ha='center', va='top')
        ax.text(84.25, yo + 9.2,
                r'$\mathbf{p}_k^0 = \frac{1}{n_k^0} \sum \bar{\mathbf{z}}_i$' + '\n' +
                r'$\mathbf{p}_k^1 = \frac{1}{n_k^1} \sum \bar{\mathbf{z}}_i$',
                fontsize=7.4, ha='center', va='top')
        ax.text(84.25, yo + 3.4, r'Dim: $2 \times 64$', fontsize=7.0, fontstyle='italic', ha='center', va='top', color=c_darkgray)


    # ----------------------------------------------------------------------
    # PRIVACY-PRESERVING INSTITUTIONAL BOUNDARY (Vertical Divider)
    # ----------------------------------------------------------------------
    boundary_x = 97.5
    ax.plot([boundary_x, boundary_x], [4, 91.5], color=c_black, linestyle=(0, (4, 4)), linewidth=2.0)

    # Privacy Banner on top
    ax.text(boundary_x, 94.0, "SECURE INSTITUTIONAL PRIVACY BOUNDARY",
            fontsize=10.5, fontweight='bold', ha='center', va='bottom')
    ax.text(boundary_x, 2.0,
            r"$\mathbf{Zero\ Raw\ Data,\ Gradients,\ or\ Model\ Weights\ Shared}\quad|\quad\mathbf{512\ Bytes\ /\ Client\ /\ Round}$",
            fontsize=8.5, fontstyle='italic', ha='center', va='top')

    # Communication Uplink / Downlink Channels crossing boundary
    for yo in [77.5, 48.0, 18.5]:
        # Uplink: Upload Prototypes
        ax.annotate('', xy=(104.5, yo + 2.5), xytext=(90.5, yo + 2.5),
                    arrowprops=dict(facecolor=c_black, edgecolor=c_black, width=1.1, headwidth=5.5, headlength=5.5))
        ax.text(boundary_x, yo + 4.3, r'Uplink: $\{\mathbf{p}_k^0, \mathbf{p}_k^1, n_k^c\}$ (512 B)',
                fontsize=7.4, ha='center', va='bottom',
                bbox=dict(boxstyle='square,pad=0.12', facecolor=c_white, edgecolor='none'))

        # Downlink: Broadcast Global Prototypes
        ax.annotate('', xy=(90.5, yo - 2.5), xytext=(104.5, yo - 2.5),
                    arrowprops=dict(facecolor=c_darkgray, edgecolor=c_darkgray, width=1.1, headwidth=5.5, headlength=5.5))
        ax.text(boundary_x, yo - 4.3, r'Downlink: $\{\bar{\mathbf{P}}^0, \bar{\mathbf{P}}^1\}$ (512 B)',
                fontsize=7.4, ha='center', va='top', color=c_darkgray,
                bbox=dict(boxstyle='square,pad=0.12', facecolor=c_white, edgecolor='none'))


    # ----------------------------------------------------------------------
    # CENTRAL FEDERATED AGGREGATION SERVER (Right Side)
    # ----------------------------------------------------------------------
    server_box = patches.FancyBboxPatch((104.5, 7), 43, 85.5,
                                        boxstyle="round,pad=0.7",
                                        facecolor=c_white, edgecolor=c_black,
                                        linewidth=1.6)
    ax.add_patch(server_box)

    # Server Title
    ax.text(126, 90.5, "Central Aggregation Server", fontsize=11.2, fontweight='bold', ha='center', va='top')
    ax.text(126, 87.8, "Decentralized Consortium Orchestrator", fontsize=8.6, fontstyle='italic', color=c_darkgray, ha='center', va='top')

    # 1. Square-Root Weighted Prototype Aggregation Box
    agg_box = patches.FancyBboxPatch((107, 51.5), 38, 33.5,
                                     boxstyle="square,pad=0.3",
                                     facecolor=c_lightgray, edgecolor=c_black, linewidth=1.2)
    ax.add_patch(agg_box)

    ax.text(126, 83.0, "Square-Root Sample-Weighted\nPrototype Aggregation",
            fontsize=9.4, fontweight='bold', ha='center', va='top')

    ax.text(126, 75.5,
            r'$\mathbf{P}^c = \frac{\sum_{k=1}^K \sqrt{n_k^c} \cdot \mathbf{p}_k^c}{\sum_{k=1}^K \sqrt{n_k^c}} \in \mathbb{R}^{64}$',
            fontsize=9.5, ha='center', va='top')

    ax.text(126, 68.5,
            r'Hypersphere Projection ($L_2$-Normalization):' + '\n' +
            r'$\bar{\mathbf{P}}^c = \frac{\mathbf{P}^c}{\|\mathbf{P}^c\|_2} \in \mathbb{S}^{63}, \quad c \in \{0, 1\}$',
            fontsize=8.5, ha='center', va='top')

    ax.text(126, 60.5,
            r'Global Consensus Dictionary:' + '\n' +
            r'$\mathcal{P}_{\mathrm{global}} = \{\bar{\mathbf{P}}^0\text{ (Normal)},\; \bar{\mathbf{P}}^1\text{ (Abnormal)}\}$',
            fontsize=8.5, ha='center', va='top', fontweight='bold')

    ax.text(126, 53.5, r'Total Broadcast Payload: 128 Floats (512 Bytes)',
            fontsize=7.5, fontstyle='italic', ha='center', va='top', color=c_darkgray)

    # Connecting Arrow: Aggregation Box -> Dual Objective Box
    ax.annotate('', xy=(126, 47.0), xytext=(126, 51.5),
                arrowprops=dict(facecolor=c_black, edgecolor=c_black, width=1.0, headwidth=5, headlength=5))

    # 2. Dual Loss Regularization Box
    loss_box = patches.FancyBboxPatch((107, 9.5), 38, 37.0,
                                      boxstyle="square,pad=0.3",
                                      facecolor=c_lightgray, edgecolor=c_black, linewidth=1.2)
    ax.add_patch(loss_box)

    ax.text(126, 44.5, "Composite Client Optimization Objective\n(Dual Prototype Guidance)",
            fontsize=9.2, fontweight='bold', ha='center', va='top')

    ax.text(126, 38.0,
            r'$\mathcal{L}_{\mathrm{total}}^k = \mathcal{L}_{\mathrm{CE}}^k + \lambda_{\mathrm{proto}}(r)\mathcal{L}_{\mathrm{proto}}^k + \lambda_{\mathrm{contrast}}(r)\mathcal{L}_{\mathrm{contrast}}^k$',
            fontsize=8.5, ha='center', va='top')

    ax.text(126, 32.5,
            r'$\mathbf{1.\ Prototype\ Alignment\ Pull\ (\mathcal{L}_{\mathrm{proto}}^k):}$' + '\n' +
            r'$\mathcal{L}_{\mathrm{proto}}^k = \frac{1}{N_B} \sum_{i=1}^{N_B} w_i \left( 1 - \cos(\bar{\mathbf{z}}_i^k, \bar{\mathbf{P}}^{y_i}) \right)$',
            fontsize=7.8, ha='center', va='top')

    ax.text(126, 23.5,
            r'$\mathbf{2.\ Contrastive\ Anchor\ Push\ (\mathcal{L}_{\mathrm{contrast}}^k):}$' + '\n' +
            r'$\mathcal{L}_{\mathrm{contrast}}^k = - \frac{1}{N_B} \sum_{i=1}^{N_B} w_i \log \left( \frac{\exp(\cos(\bar{\mathbf{z}}_i^k, \bar{\mathbf{P}}^{y_i}) / \tau)}{\sum_{c} \exp(\cos(\bar{\mathbf{z}}_i^k, \bar{\mathbf{P}}^c) / \tau)} \right)$',
            fontsize=7.8, ha='center', va='top')

    ax.text(126, 14.5,
            r'$\mathbf{3.\ Adaptive\ Decay\ Schedule:}$' + ' ' + r'$\lambda(r) = \max(0.3, 1.0 - \gamma \cdot r)$' + '\n' +
            r'$\mathbf{4.\ Class-Balanced\ CE:}$' + ' ' + r'$\mathcal{L}_{\mathrm{CE}}^k \text{ with weights } w(c) = \frac{N_B}{2 \cdot n_k^c}$',
            fontsize=7.5, ha='center', va='top')


    # Save figure
    out_png = 'report_images/fedcardio_architecture_bw.png'
    out_pdf = 'report_images/fedcardio_architecture_bw.pdf'
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(out_pdf, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Successfully generated clean diagram at:\n- {out_png}\n- {out_pdf}")

if __name__ == '__main__':
    generate_improved_diagram()
