import os
import zipfile

IMAGES = {
    "logo.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="brainGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ec4899" />
      <stop offset="50%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
  </defs>
  <path d="M100 30 C70 30 50 50 50 75 C35 80 25 95 25 115 C25 140 45 160 70 160 C80 160 90 155 100 145 C110 155 120 160 130 160 C155 160 175 140 175 115 C175 95 165 80 150 75 C150 50 130 30 100 30 Z" fill="url(#brainGrad)"/>
  <path d="M100 45 V135 M75 60 C85 75 85 95 75 110 M125 60 C115 75 115 95 125 110" stroke="#ffffff" stroke-width="4" stroke-linecap="round" fill="none" opacity="0.6"/>
  <circle cx="70" cy="70" r="4" fill="#ffffff"/>
  <circle cx="130" cy="70" r="4" fill="#ffffff"/>
  <circle cx="60" cy="110" r="4" fill="#ffffff"/>
  <circle cx="140" cy="110" r="4" fill="#ffffff"/>
</svg>''',

    # ILUSTRAÇÃO GRANDE DA SEÇÃO HERÓI (Cérebro IA + Livro + Bandeiras + Lâmpada + Fórmulas)
    "hero_illustration.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 420" width="100%" height="100%">
  <defs>
    <linearGradient id="heroBrainGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e" />
      <stop offset="50%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
    <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Anéis Orbitais de Conhecimento -->
  <ellipse cx="260" cy="200" rx="190" ry="110" fill="none" stroke="#60a5fa" stroke-width="2" stroke-dasharray="6,6" opacity="0.5"/>
  <ellipse cx="260" cy="200" rx="140" ry="170" fill="none" stroke="#34d399" stroke-width="1.5" stroke-dasharray="4,4" opacity="0.4"/>
  
  <!-- Livro Aberto (Base) -->
  <path d="M 110 330 Q 260 290 260 350 Q 260 290 410 330 V 230 Q 260 190 260 250 Q 260 190 110 230 Z" fill="#ffffff" stroke="#cbd5e1" stroke-width="4"/>
  <path d="M 120 320 Q 255 285 255 340 M 400 320 Q 265 285 265 340" fill="none" stroke="#94a3b8" stroke-width="2"/>

  <!-- Cérebro Central Iluminado -->
  <g filter="url(#glowEffect)">
    <circle cx="260" cy="180" r="52" fill="url(#heroBrainGrad)"/>
  </g>
  <path d="M260 142 V218 M238 158 C248 175 248 192 238 208 M282 158 C272 175 272 192 282 208" stroke="#ffffff" stroke-width="3" stroke-linecap="round" fill="none" opacity="0.8"/>
  
  <!-- Selo "AI" em Azul -->
  <circle cx="295" cy="138" r="20" fill="#2563eb" stroke="#ffffff" stroke-width="2"/>
  <text x="295" y="144" fill="#ffffff" font-family="Arial, sans-serif" font-weight="bold" font-size="13" text-anchor="middle">AI</text>

  <!-- Bandeira do Brasil (Top Left) -->
  <g transform="translate(130, 80)">
    <rect width="54" height="36" rx="5" fill="#16a34a"/>
    <polygon points="27,4 50,18 27,32 4,18" fill="#facc15"/>
    <circle cx="27" cy="18" r="8" fill="#2563eb"/>
  </g>

  <!-- Bandeira do Reino Unido / UK (Top Right) -->
  <g transform="translate(330, 80)">
    <rect width="54" height="36" rx="5" fill="#1e3a8a"/>
    <path d="M0,0 L54,36 M54,0 L0,36" stroke="#ffffff" stroke-width="6"/>
    <path d="M0,0 L54,36 M54,0 L0,36" stroke="#dc2626" stroke-width="3"/>
    <path d="M27,0 V36 M0,18 H54" stroke="#ffffff" stroke-width="10"/>
    <path d="M27,0 V36 M0,18 H54" stroke="#dc2626" stroke-width="6"/>
  </g>

  <!-- Ícone da Lâmpada (Ideia - Bottom Right) -->
  <g transform="translate(345, 235)">
    <circle cx="22" cy="22" r="20" fill="#f59e0b"/>
    <path d="M16 16 C16 11 28 11 28 16 C28 21 24 23 24 27 H20 C20 23 16 21 16 16 Z" fill="#ffffff"/>
    <rect x="20" y="29" width="4" height="3" fill="#ffffff"/>
  </g>

  <!-- Fórmula Matemática (Bottom Left) -->
  <g transform="translate(135, 230)">
    <rect width="70" height="38" rx="8" fill="#8b5cf6"/>
    <text x="35" y="24" fill="#ffffff" font-family="Courier, monospace" font-weight="bold" font-size="12" text-anchor="middle">(a²+b²)</text>
  </g>
</svg>''',

    "step1_disciplinas.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect x="15" y="20" width="70" height="60" rx="10" fill="#dbeafe" stroke="#2563eb" stroke-width="3"/>
  <rect x="25" y="32" width="50" height="8" rx="4" fill="#2563eb"/>
  <rect x="25" y="48" width="35" height="6" rx="3" fill="#93c5fd"/>
  <rect x="25" y="60" width="40" height="6" rx="3" fill="#93c5fd"/>
</svg>''',

    "step2_perguntas.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <path d="M20 25 C20 16.7 26.7 10 35 10 H65 C73.3 10 80 16.7 80 25 V50 C80 58.3 73.3 65 65 65 H45 L25 80 V65 C22 65 20 60 20 50 Z" fill="#2563eb"/>
  <text x="50" y="46" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="28" text-anchor="middle">?</text>
  <circle cx="75" cy="20" r="14" fill="#10b981"/>
  <text x="75" y="25" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="13" text-anchor="middle">3</text>
</svg>''',

    "step3_assine.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <path d="M50 15 C65 15 75 30 75 50 L65 70 H35 L25 50 C25 30 35 15 50 15 Z" fill="#10b981"/>
  <polygon points="50,25 58,40 42,40" fill="#ffffff"/>
  <circle cx="50" cy="52" r="8" fill="#ffffff"/>
  <path d="M30 70 L20 85 L35 78" fill="#ef4444"/>
  <path d="M70 70 L80 85 L65 78" fill="#ef4444"/>
</svg>''',

    "portugues.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <rect width="120" height="120" rx="24" fill="#16a34a"/>
  <path d="M60 20 L100 60 L60 100 L20 60 Z" fill="#facc15"/>
  <circle cx="60" cy="60" r="22" fill="#2563eb"/>
  <path d="M40 60 Q 60 50 80 60" stroke="#ffffff" stroke-width="3" fill="none"/>
</svg>''',

    "ingles.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <rect width="120" height="120" rx="24" fill="#0284c7"/>
  <circle cx="60" cy="60" r="38" fill="#0369a1" stroke="#ffffff" stroke-width="4"/>
  <path d="M30 60 H90 M60 30 V90 M38 40 Q 60 60 38 80 M82 40 Q 60 60 82 80" stroke="#ffffff" stroke-width="3" fill="none"/>
</svg>''',

    "matematica.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <rect width="120" height="120" rx="24" fill="#7c3aed"/>
  <text x="38" y="48" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="30" text-anchor="middle">+</text>
  <text x="82" y="48" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="30" text-anchor="middle">−</text>
  <text x="38" y="90" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="30" text-anchor="middle">×</text>
  <text x="82" y="90" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="30" text-anchor="middle">=</text>
</svg>''',

    "programacao.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <rect width="120" height="120" rx="24" fill="#0f172a"/>
  <rect x="20" y="30" width="80" height="60" rx="8" fill="#1e293b" stroke="#38bdf8" stroke-width="3"/>
  <text x="60" y="66" fill="#38bdf8" font-family="monospace" font-weight="bold" font-size="22" text-anchor="middle">&lt;/&gt;</text>
</svg>''',

    "historia.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <rect width="120" height="120" rx="24" fill="#d97706"/>
  <path d="M35 30 H85 M40 30 V85 M60 30 V85 M80 30 V85 M30 85 H90 M25 95 H95" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>
</svg>'''
}

def generate_assets():
    assets_dir = "assets"
    os.makedirs(assets_dir, exist_ok=True)
    zip_filename = "imagens_mente_saber.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in IMAGES.items():
            filepath = os.path.join(assets_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            zip_file.write(filepath, arcname=filename)
            print(f"✅ Gerado: {filepath}")

    print(f"\n🎉 Sucesso! Todas as imagens foram atualizadas na pasta '{assets_dir}/'.")

if __name__ == "__main__":
    generate_assets()