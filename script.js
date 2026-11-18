/* =============================================================================
   HA — Personal Digital Identity
   script.js
   -----------------------------------------------------------------------------
   محرك التفاعل متعدد اللغات في موقع السيرة الذاتية الرقمية.
   لا يعتمد على أي مكتبة خارجية (Vanilla JavaScript).

   محتويات الملف:
     01. أدوات مساعدة (Utilities)
     02. قاموس الترجمة (Translations Dictionary)
     03. محرك تعدد اللغات (I18n Engine)
     04. إدارة الوضع الليلي/النهاري (Theme Manager)
     05. التنبيهات المنبثقة (Toast)
     06. قائمة الجوال (Mobile Navigation)
     07. التمرير السلس (Smooth Scroll)
     08. شريط تقدم القراءة (Reading Progress)
     09. تحديد القسم النشط (Scroll Spy + Nav Indicator)
     10. حركات الظهور عند التمرير (IntersectionObserver)
     11. تأثير الكتابة المتحرك (Typing Effect)
     12. تأثيرات البطاقات التفاعلية (Tilt / Hover)
     13. زر العودة إلى الأعلى (Back to Top)
     14. نافذة تفاصيل المشروع (Project Modal)
     15. الطباعة وتصدير PDF (Print to PDF)
     16. سنة التذييل + حالة الرأس
     17. تفضيل تقليل الحركة (Reduced Motion)
     18. تهيئة الصفحة (Init)
   ========================================================================== */

(function () {
  'use strict';

  /* ===========================================================================
     01. أدوات مساعدة
     =========================================================================== */

  const $  = (selector, scope) => (scope || document).querySelector(selector);
  const $$ = (selector, scope) => Array.from((scope || document).querySelectorAll(selector));

  /** هل يفضّل المستخدم تقليل الحركة؟ */
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /** هل الجهاز يدعم التمرير بالماوس (أجهزة سطح المكتب)؟ */
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)');

  /** تأخير التنفيذ حتى الإطار التالي لتفادي التكرار المتكرر. */
  function throttleRaf(callback) {
    let ticking = false;
    return function (...args) {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        ticking = false;
        callback.apply(this, args);
      });
    };
  }

  /** برمجة زمنية تُرجع وعدًا. */
  function delay(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  /**
   * الوضع الساكن (?static=1)
   * يُعطّل حركات الدخول ويعرض النصوص النهائية — مفيد لإنشاء صور مشاركة
   * وملفات PDF ثابتة، وللتعامل الآلي مع الصفحة.
   */
  const STATIC_MODE = (function () {
    try {
      return new URLSearchParams(window.location.search).has('static');
    } catch (error) {
      return false;
    }
  })();


  /* ===========================================================================
     02. قاموس الترجمة — النسخة الإنجليزية
     -----------------------------------------------------------------------
     المحتوى العربي هو النسخة الأساسية الموجودة داخل ملف HTML،
     وتُحفظ تلقائيًا عند التهيئة للاستعادة عند العودة إلى العربية.
     =========================================================================== */
  const TRANSLATIONS = {
    en: {
      /* ---------- التنقل ---------- */
      'nav.home': 'Home',
      'nav.about': 'About',
      'nav.personality': 'Personality',
      'nav.skills': 'Skills',
      'nav.projects': 'Projects',
      'nav.education': 'Education',
      'nav.interests': 'Interests',
      'nav.vision': 'Vision',
      'nav.contact': 'Contact',
      'nav.cta': 'Contact me',
      'brand.word': 'HADEEL',

      /* ---------- الواجهة الرئيسية ---------- */
      'hero.name1': 'Hadeel',
      'hero.name2': 'Abdulqawi',
      'hero.quote': 'I learn to understand, I understand to create, and I create to leave an impact.',
      'hero.text': 'I believe real knowledge begins with curiosity, grows through understanding and experience, and turns into achievement once it finds its way into application. I strive to combine analytical thinking with technical creativity, and to explore the possibilities that artificial intelligence offers for creating ideas and solutions of genuine value.',
      'hero.btn.projects': 'Explore My Work',
      'hero.btn.about': 'Get to Know Me',
      'hero.btn.pdf': 'Download CV (PDF)',
      'hero.fact1.label': 'Specialty',
      'hero.fact1.value': 'Artificial Intelligence',
      'hero.fact2.label': 'University',
      'hero.fact2.value': 'Islamic University of Minnesota — Online',
      'hero.fact3.label': 'Status',
      'hero.fact3.value': 'Bachelor’s — Undergraduate student',
      'hero.portrait.alt': 'Personal photo space for Hadeel Abdulqawi — replaceable from the images folder',
      'hero.chip1': 'Artificial Intelligence',
      'hero.chip2': 'Interface Design',
      'hero.chip3': 'Web Development',
      'hero.scroll': 'Scroll down',

      /* ---------- من أنا ---------- */
      'about.eyebrow': '01 — About',
      'about.title': 'Who am I?',
      'about.lead': 'I am <strong>Hadeel Abdulqawi</strong>, an undergraduate student majoring in Artificial Intelligence, with a passion for learning and exploration, and a growing fascination with technology, design, and digital innovation.',
      'about.p1': 'I believe excellence does not begin with knowing everything, but with having the desire to discover what we do not know, the ability to ask questions, the pursuit of deeper answers, and the refusal to settle for surface-level information.',
      'about.p2': 'I lean toward understanding and analysis rather than memorization and rote learning, and I enjoy breaking complex ideas into simple parts, then rebuilding them in a clear and practical way. I believe every new skill I acquire is an additional step toward building a more mature academic and professional character.',
      'about.p3': 'The world of digital design and web development draws me in, and I find real joy in turning ideas into visual interfaces that combine beauty, organization, and ease of use. Artificial intelligence intrigues me as well for the wide possibilities it opens in information analysis, solution development, and reshaping the way we work and think.',
      'about.p4': 'I do not view my university journey as merely a stage for obtaining a degree, but as an opportunity to build a strong scientific foundation, discover my capabilities, and develop my skills step by step — through study, experience, and practice.',
      'about.p5': 'I aspire to combine logical thinking with a creative sensibility, and to be able, in the future, to contribute to the development of technology projects that carry real value, deliver useful solutions, and leave a positive impact.',
      'about.quote': '“I believe that behind every question lies a chance for a new discovery.”',
      'about.quote.cite': 'From my daily reflections',
      'about.visual.alt': 'Portrait of Hadeel Abdulqawi',
      'about.visual.text': '«Curiosity is the starting point,<br />application is the destination.»',
      'about.sig.name': 'Hadeel',
      'about.sig.role': 'AI student · Interface developer',

      /* ---------- ما الذي يميزني ---------- */
      'distinct.eyebrow': 'What sets me apart?',
      'distinct.title': '“My way of thinking is the beginning of every achievement”',
      'distinct.p1': 'I am not always looking for <em class="mark">the easiest path</em>, but for <em class="mark">the path that grants me deeper understanding</em> and genuine experience.',
      'distinct.p2': 'I love to see the result of what I learn in front of me; <em class="mark">an idea becomes a design</em>, information becomes an application, and a problem becomes an opportunity to find a solution.',
      'distinct.p3': 'I believe that combining <em class="mark">technical precision</em> with <em class="mark">creative taste</em> produces work that stands apart, and that real progress is tied not to where we start, but to <em class="mark">the persistence we choose</em>.',

      /* ---------- شخصيتي ---------- */
      'personality.eyebrow': '02 — Personality',
      'personality.title': 'My personality and way of thinking',
      'personality.subtitle': 'Four pillars define me: how I understand, how I create, how I learn, and where I am heading.',
      'personality.c1.title': 'Analytical Mindset',
      'personality.c1.text': 'I love understanding the reasons behind things, and never settle for knowing the result without understanding how it was reached.',
      'personality.c2.title': 'Creative Spirit',
      'personality.c2.text': 'I enjoy inventing ideas, refining details, and turning concepts into visible work.',
      'personality.c3.title': 'Intellectual Curiosity',
      'personality.c3.text': 'I love researching and exploring, and reaching a clear understanding before moving to the next step.',
      'personality.c4.title': 'Continuous Ambition',
      'personality.c4.text': 'I believe in gradual progress, and that great achievements begin with small, steady steps.',

      /* ---------- المهارات ---------- */
      'skills.eyebrow': '03 — Skills',
      'skills.title': 'Skills',
      'skills.subtitle': 'Skills I have genuinely acquired through study and practice — listed at my current level of learning rather than claiming levels I do not hold.',
      'skills.g1.title': 'Technical Skills',
      'skills.g1.meta': 'Technical Skills',
      'skills.g2.title': 'Creative Skills',
      'skills.g2.meta': 'Creative Skills',
      'skills.g3.title': 'Personal Skills',
      'skills.g3.meta': 'Personal Skills',
      'skills.s1.name': 'HTML',
      'skills.s1.tag': 'Page structure',
      'skills.s2.name': 'CSS',
      'skills.s2.tag': 'Styling & responsive design',
      'skills.s3.name': 'Java',
      'skills.s3.tag': 'Programming fundamentals',
      'skills.s4.name': 'SQL',
      'skills.s4.tag': 'Database fundamentals',
      'skills.s5.name': 'AI Fundamentals',
      'skills.s5.tag': 'Academic major',
      'skills.s6.name': 'Digital Tools',
      'skills.s6.tag': 'Daily practice',
      'skills.s7.name': 'Digital Design',
      'skills.s7.tag': 'Visual principle',
      'skills.s8.name': 'Website UI Design',
      'skills.s8.tag': 'User experience',
      'skills.s9.name': 'Canva',
      'skills.s9.tag': 'Design tooling',
      'skills.s10.name': 'Content Formatting',
      'skills.s10.tag': 'Visual communication',
      'skills.s11.name': 'Presentation Design',
      'skills.s11.tag': 'Professional delivery',
      'skills.s12.name': 'Analytical Thinking',
      'skills.s12.tag': 'Thinking style',
      'skills.s13.name': 'Problem Solving',
      'skills.s13.tag': 'Practical application',
      'skills.s14.name': 'Research & Self-learning',
      'skills.s14.tag': 'Ongoing practice',
      'skills.s15.name': 'Organizing Ideas',
      'skills.s15.tag': 'Structure & building',
      'skills.s16.name': 'Attention to Detail',
      'skills.s16.tag': 'Precision in execution',
      'skills.s17.name': 'Continuous Learning',
      'skills.s17.tag': 'A lasting principle',
      'skills.quote': '“Beauty in design, precision in thinking, and value in the result.”',

      /* ---------- المشاريع ---------- */
      'projects.eyebrow': '04 — Projects',
      'projects.title': 'Project Gallery',
      'projects.subtitle': 'Five works combining interface design, programming, and data modeling — each one different from the others.',
      'projects.more': 'Project details',
      'projects.note': 'Status: internal design prototype — work in progress, not published online yet.',
      'projects.note2': 'Status: academic project within the requirements of the program.',
      'projects.p1.category': 'Interface design · Corporate site',
      'projects.p1.title': 'Building Materials Company Website',
      'projects.p1.text': 'Designing a corporate digital interface to showcase a building materials company’s products and services, with close attention to visual order and ease of access to information.',
      'projects.p1.tag1': 'Interface design',
      'projects.p1.tag2': 'HTML / CSS',
      'projects.p1.tag3': 'Product showcase',
      'projects.p1.alt': 'Building materials and construction — interface design for a building materials company',
      'projects.p1.detail.p': 'A complete interface concept for a building materials company, built on a clear information sequence: a company overview, the main product categories, dedicated service sections, and a direct contact area.',
      'projects.p1.detail.l1': 'Products organized into a visual grid with clear imagery and proportions.',
      'projects.p1.detail.l2': 'A direct browsing path: Home → Categories → Product.',
      'projects.p1.detail.l3': 'A company profile page focused on experience and contact channels.',
      'projects.p1.detail.l4': 'Colors inspired by the industrial identity of materials: deep burgundy and sandy gold.',
      'projects.p2.category': 'Digital experience · Hospitality & luxury',
      'projects.p2.title': 'Sheikha Hospitality & Luxury Website',
      'projects.p2.text': 'Designing a digital experience for a hotel website that conveys luxury and hospitality, presenting the rooms, services, and facilities.',
      'projects.p2.tag1': 'Hospitality',
      'projects.p2.tag2': 'UI / UX',
      'projects.p2.tag3': 'Room showcase',
      'projects.p2.alt': 'Luxury resort and hotel — a digital experience reflecting luxury and hospitality',
      'projects.p2.detail.p': 'A visual digital experience for a hotel website, designed to transfer the feeling of luxury and hospitality to the screen through the contrast between generous white space and wide panoramic imagery.',
      'projects.p2.detail.l1': 'A rooms and facilities showcase with clear headings and a concise description for each item.',
      'projects.p2.detail.l2': 'A services section covering the entire experience from arrival to departure.',
      'projects.p2.detail.l3': 'An ivory and gold color system conveying elegance without excess.',
      'projects.p2.detail.l4': 'Harmonized Arabic typography with comfortable spacing for mobile reading.',
      'projects.p3.category': 'Programming · OOP concepts',
      'projects.p3.title': 'Java OOP Concepts Application',
      'projects.p3.text': 'Applying the fundamentals of object-oriented programming through classes, properties, methods, and organized code.',
      'projects.p3.tag1': 'Java',
      'projects.p3.tag2': 'OOP',
      'projects.p3.tag3': 'Structuring',
      'projects.p3.alt': 'A programming screen showing Java code structure — an application of object-oriented programming concepts',
      'projects.p3.back.category': 'Technical details',
      'projects.p3.back.l1': 'Designing classes with private and protected properties.',
      'projects.p3.back.l2': 'Using methods and constructors to initialize objects.',
      'projects.p3.back.l3': 'Applying the principle of encapsulation when handling data.',
      'projects.p3.back.l4': 'Organizing code into clear files with separated responsibilities.',
      'projects.p3.detail.p': 'An applied project focused on translating theoretical object-oriented programming concepts into runnable, well-organized code.',
      'projects.p3.detail.l1': 'Building a class structure where each class represents an entity from the real problem.',
      'projects.p3.detail.l2': 'Using inheritance and abstraction to remove duplication in the code.',
      'projects.p3.detail.l3': 'Adding internal documentation explaining the purpose of every class and function.',
      'projects.p4.category': 'Databases · Modeling',
      'projects.p4.title': 'Hotel System Database',
      'projects.p4.text': 'Designing a database that includes the tables, fields, and primary keys, and organizes the data records.',
      'projects.p4.tag1': 'SQL',
      'projects.p4.tag2': 'ERD',
      'projects.p4.tag3': 'Normalization',
      'projects.p4.alt': 'Servers and databases — design of a hotel system database',
      'projects.p4.detail.p': 'A database schema for a hotel system that links rooms to customer bookings, built on the relational entity model (ERD).',
      'projects.p4.detail.l1': 'Tables: rooms, room types, guests, reservations, payments, and services.',
      'projects.p4.detail.l2': 'Primary and foreign keys connecting reservation records to guest and room data.',
      'projects.p4.detail.l3': 'Table normalization to reduce data duplication and preserve integrity.',
      'projects.p4.detail.l4': 'Defining appropriate data types and constraints for every field.',
      'projects.p5.category': 'Research · Artificial intelligence',
      'projects.p5.title': 'Artificial Intelligence Research',
      'projects.p5.text': 'Studying the impact of artificial intelligence on decision-making and everyday life, and exploring its relationship with people and society.',
      'projects.p5.tag1': 'AI',
      'projects.p5.tag2': 'Case study',
      'projects.p5.tag3': 'Analysis',
      'projects.p5.alt': 'An AI robot — research on the impact of artificial intelligence on decision-making',
      'projects.p5.detail.p': 'Research that connects the theoretical aspects of artificial intelligence to its everyday reality, with a focus on its influence on decision-making and its relationship with people and society.',
      'projects.p5.detail.l1': 'A review of the pillars of AI, machine learning, and data analysis.',
      'projects.p5.detail.l2': 'Studying real examples from recommendation, diagnostics, and assistive systems.',
      'projects.p5.detail.l3': 'Analyzing the ethical and social impact on the individual and on society.',
      'projects.p5.detail.l4': 'Drawing practical recommendations for engaging with these technologies consciously.',
      'projects.quote': '“Every new project is a space where I discover a new capability within myself.”',

      /* ---------- التعليم ---------- */
      'education.eyebrow': '05 — Education',
      'education.title': 'Academic Path',
      'education.stage.label': 'Stage',
      'education.stage.value': 'Bachelor’s Degree',
      'education.status': 'Undergraduate student',
      'education.specialty.label': 'Major',
      'education.specialty.value': 'Artificial Intelligence',
      'education.university.label': 'University',
      'education.university.value': 'Islamic University of Minnesota — United States',
      'education.mode.label': 'Study mode',
      'education.mode.value': 'Online / distance learning',
      'education.status.label': 'Status',
      'education.status.value': 'Undergraduate student',
      'education.interests.title': 'Key Academic Interests',
      'education.i1': 'Computer Science Fundamentals',
      'education.i2': 'Programming',
      'education.i3': 'Artificial Intelligence',
      'education.i4': 'Data Analysis',
      'education.i5': 'Databases',
      'education.i6': 'Design & Web Development',

      /* ---------- الاهتمامات ---------- */
      'interests.eyebrow': '06 — Interests',
      'interests.title': '“Areas where I explore the future”',
      'interests.subtitle': 'Seven technology fields that intersect with my major and interests, and whose progress I follow continuously.',
      'interests.c1.title': 'Artificial Intelligence',
      'interests.c1.text': 'My university major, and the field where I follow the evolution of models and their practical applications.',
      'interests.c2.title': 'Machine Learning',
      'interests.c2.text': 'How does a machine learn from data? A favorite space for hands-on exploration.',
      'interests.c3.title': 'Data Analysis',
      'interests.c3.text': 'Turning raw numbers into insights that are usable and actionable.',
      'interests.c4.title': 'UI/UX Design',
      'interests.c4.text': 'The bridge between logical thinking and aesthetic sense — an interface understood at a glance.',
      'interests.c5.title': 'Web Development',
      'interests.c5.text': 'Building pages that are fast, well organized, and responsive on every screen size.',
      'interests.c6.title': 'Modern Digital Technologies',
      'interests.c6.text': 'New tools and models that reshape the way we work and communicate.',
      'interests.c7.title': 'Innovation & Smart Solutions',
      'interests.c7.text': 'Turning a problem into a solution, and an idea into something people can try.',
      'interests.quote': '“I do not study to collect information, but to turn it into knowledge I can actually use.”',

      /* ---------- الرؤية ---------- */
      'vision.eyebrow': '07 — Vision',
      'vision.title': '“My journey does not stop at learning — it starts there”',
      'vision.lead': 'I aspire to be part of the technological future, not merely a recipient of its developments.',
      'vision.p1': 'I seek to deepen my work in artificial intelligence, and to grow my capabilities in programming, data analysis, and digital design — building experience that unites academic knowledge with practical application.',
      'vision.p2': 'I aspire to deliver projects that reflect my ideas and abilities, and to take part in inventing technology solutions that serve people and keep pace with the needs of the future.',
      'vision.p3': 'My journey is still at its beginning, but I believe that a conscious start, continuous learning, and persistence in growing are enough to shape a different future.',
      'vision.pillar1': 'Deepening AI expertise',
      'vision.pillar2': 'Programming & data analysis',
      'vision.pillar3': 'Digital design',
      'vision.pillar4': 'Solutions that serve people',
      'vision.card.label': 'Goal',
      'vision.card.title': 'Knowledge applied to<br />building things that matter',
      'vision.quote': '“Ambition is not about arriving quickly, but about arriving while possessing the knowledge that deserves the arrival.”',

      /* ---------- التواصل ---------- */
      'contact.eyebrow': '08 — Contact',
      'contact.title': 'Let’s build something worth it',
      'contact.subtitle': 'I would be glad to connect and exchange ideas and opportunities. Choose whichever channel suits you:',
      'contact.wa.label': 'Fastest way to reach me',
      'contact.wa.title': 'I would be glad to connect and exchange ideas and opportunities.',
      'contact.wa.btn': 'Message me on WhatsApp',
      'contact.c1.label': 'Direct call',
      'contact.c2.label': 'Email',
      'contact.c3.label': 'WhatsApp',
      'contact.c3.value': 'A direct and quick conversation',
      'contact.c4.label': 'Name',
      'contact.c4.value': 'Hadeel',

      /* ---------- التذييل ---------- */
      'footer.name': 'Hadeel',
      'footer.closing': '“Every beginning carries a new possibility, and every conscious step brings us closer to the version of ourselves we aspire to become.”',
      'footer.nav.title': 'Sections',
      'footer.contact.title': 'Get in Touch',
      'footer.wa': 'WhatsApp',
      'footer.call': 'Direct call',
      'footer.rights': 'Hadeel — All rights reserved.',
      'footer.credits': 'Designed & built by <strong>HADEEL</strong> · HTML5 · CSS3 · JavaScript',

      /* ---------- الطباعة ---------- */
      'print.name': 'Hadeel',
      'print.role': 'Bachelor’s student in Artificial Intelligence | Passionate about technology and digital design'
    }
  };

  /** بيانات وصفية تتبدّل مع اللغة (العنوان ووصف الصفحة) */
  const META = {
    ar: {
      title: 'Hadeel | سيرة ذاتية رقمية — HADEEL Personal Digital Identity',
      description: 'Hadeel — السيرة الذاتية الرقمية لهُديل عبدالقوي، طالبة بكالوريوس في الظكاء الاصطناعي، مهتمة بالتقنية والتصميم الرقمي. معرض مشارع، مهارات، تعليم، وروابط تواصل مباشرة.',
      ogTitle: 'Hadeel | HADEEL — Personal Digital Identity',
      ogDescription: 'طالبة بكالوريوس في الذكاء الاصطناعي | مهتمة بالتقنية والتصميم الرقمي.',
      twTitle: 'Hadeel | HADEEL Portfolio',
      twDescription: 'سيرة ذاتية رقمية فاخرة تجمع بين الفكر الأكاديمي والطموح التقني.'
    },
    en: {
      title: 'Hadeel Abdulqawi | Digital CV — HADEEL Personal Digital Identity',
      description: 'The digital CV of Hadeel Abdulqawi, undergraduate student in Artificial Intelligence, passionate about technology and digital design. Project gallery, skills, education, and direct contact links.',
      ogTitle: 'Hadeel Abdulqawi | HADEEL — Personal Digital Identity',
      ogDescription: 'Bachelor’s student in Artificial Intelligence | Passionate about technology and digital design.',
      twTitle: 'Hadeel Abdulqawi | HADEEL Portfolio',
      twDescription: 'A premium digital CV blending academic thinking with technical ambition.'
    }
  };

  /** نصوص المسمى المهني لكل لغة (تستخدمها حركة الكتابة) */
  const ROLES = {
    ar: [
      { text: 'طالبة بكالوريوس في الذكاء الاصطناعي', speed: 58, pause: 380 },
      { text: ' | ', speed: 26, pause: 120 },
      { text: 'مهتمة بالتقنية والتصميم الرقمي', speed: 48, pause: 500 }
    ],
    en: [
      { text: 'Bachelor’s student in Artificial Intelligence', speed: 44, pause: 380 },
      { text: ' | ', speed: 26, pause: 120 },
      { text: 'Passionate about technology and digital design', speed: 38, pause: 500 }
    ]
  };


  /* ===========================================================================
     03. محرك تعدد اللغات (I18n)
     =========================================================================== */

  const I18n = (function () {
    const STORAGE_KEY = 'ha-portfolio-lang';
    let current = 'ar';

    /** حفظ النسخة الأصلية (العربية) من كل عنصر قابل للترجمة. */
    function capture() {
      $$('[data-i18n]').forEach((element) => {
        if (element.dataset.i18nAr === undefined) {
          element.dataset.i18nAr = element.innerHTML;
        }
      });
      $$('[data-i18n-alt]').forEach((element) => {
        if (element.dataset.i18nAltAr === undefined) {
          element.dataset.i18nAltAr = element.getAttribute('alt') || '';
        }
      });
    }

    /** تطبيق الترجمات على مستوى المستند. */
    function translate(lang) {
      const map = TRANSLATIONS[lang] || {};

      $$('[data-i18n]').forEach((element) => {
        const key = element.getAttribute('data-i18n');
        if (lang === 'ar') {
          element.innerHTML = element.dataset.i18nAr;
        } else if (Object.prototype.hasOwnProperty.call(map, key)) {
          element.innerHTML = map[key];
        }
      });

      $$('[data-i18n-alt]').forEach((element) => {
        const key = element.getAttribute('data-i18n-alt');
        if (lang === 'ar') {
          element.setAttribute('alt', element.dataset.i18nAltAr);
        } else if (Object.prototype.hasOwnProperty.call(map, key)) {
          element.setAttribute('alt', map[key]);
        }
      });
    }

    /** تحديث وسوم الميتا واسم الصفحة. */
    function updateMeta(lang) {
      const meta = META[lang] || META.ar;
      document.title = meta.title;

      const set = (selector, attribute, value) => {
        const element = $(selector);
        if (element) element.setAttribute(attribute, value);
      };

      set('#metaDescription', 'content', meta.description);
      set('#ogTitle', 'content', meta.ogTitle);
      set('#ogDescription', 'content', meta.ogDescription);
      set('#twTitle', 'content', meta.twTitle);
      set('#twDescription', 'content', meta.twDescription);

      const ogLocale = $('meta[property="og:locale"]');
      if (ogLocale) ogLocale.setAttribute('content', lang === 'ar' ? 'ar_SA' : 'en_US');
    }

    /** تحديث حالة زر مبدّل اللغة. */
    function updateToggle(lang) {
      $$('[data-lang-opt]').forEach((option) => {
        option.classList.toggle('is-active', option.getAttribute('data-lang-opt') === lang);
      });
    }

    /** تطبيق اللغة كاملة على الصفحة. */
    function apply(lang) {
      current = lang;
      const root = document.documentElement;

      root.setAttribute('lang', lang);
      root.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
      root.setAttribute('data-lang', lang);

      translate(lang);
      updateMeta(lang);
      updateToggle(lang);

      // إعادة تشغيل تأثير الكتابة باللغة الجديدة
      TypingEffect.setLanguage(lang);

      // إعادة حساب مواضع شريط التنقل (تتغيّر أطوال النصوص)
      window.setTimeout(() => {
        NavIndicator.update();
        ScrollSpy.update();
      }, 60);

      try {
        window.localStorage.setItem(STORAGE_KEY, lang);
      } catch (error) {
        /* التخزين غير متاح */
      }
    }

    function init() {
      capture();

      let saved = null;
      try {
        saved = window.localStorage.getItem(STORAGE_KEY);
      } catch (error) {
        saved = null;
      }

      // الأولوية: معامل الرابط ?lang=en  ثم  التفضيل المحفوظ  ثم  العربية
      let requested = null;
      try {
        requested = new URLSearchParams(window.location.search).get('lang');
      } catch (error) {
        requested = null;
      }

      const lang = (requested === 'en' || requested === 'ar')
        ? requested
        : (saved === 'en' || saved === 'ar' ? saved : 'ar');

      apply(lang);

      const toggle = $('#langToggle');
      if (toggle) {
        toggle.addEventListener('click', function (event) {
          const option = event.target.closest('[data-lang-opt]');
          if (!option) return;
          const next = option.getAttribute('data-lang-opt');
          if (next === current) return;
          apply(next);
          Toast.show(next === 'en' ? 'Language switched to English' : 'تم التبديل إلى العربية');
        });
      }
    }

    return { init, apply, get current() { return current; } };
  })();


  /* ===========================================================================
     04. إدارة الوضع الليلي / النهاري
     -----------------------------------------------------------------------
     1) تبديل بين الوضعين، 2) حفظ التفضيل في LocalStorage.
     =========================================================================== */

  const ThemeManager = (function () {
    const STORAGE_KEY = 'ha-portfolio-theme';
    const root = document.documentElement;
    const toggle = $('#themeToggle');

    const themeColorMeta = (function createMeta() {
      let meta = $('meta[name="theme-color"]');
      if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute('name', 'theme-color');
        document.head.appendChild(meta);
      }
      return meta;
    })();

    function currentTheme() {
      return root.getAttribute('data-theme') || 'light';
    }

    function apply(theme) {
      root.setAttribute('data-theme', theme);
      themeColorMeta.setAttribute('content', theme === 'dark' ? '#17100F' : '#F8F5EF');

      if (toggle) {
        const isDark = theme === 'dark';
        toggle.setAttribute('aria-pressed', String(isDark));
        toggle.setAttribute('aria-label', isDark ? 'تفعيل الوضع النهاري' : 'تفعيل الوضع الليلي');
        toggle.title = isDark ? 'تفعيل الوضع النهاري' : 'تفعيل الوضع الليلي';
      }
    }

    function init() {
      let saved = null;
      try {
        saved = window.localStorage.getItem(STORAGE_KEY);
      } catch (error) {
        saved = null;
      }

      // معامل الرابط ?theme=dark|light يتقدّم على التفضيل المحفوظ
      let requested = null;
      try {
        requested = new URLSearchParams(window.location.search).get('theme');
      } catch (error) {
        requested = null;
      }

      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = (requested === 'dark' || requested === 'light')
        ? requested
        : (saved || (prefersDark ? 'dark' : 'light'));

      apply(theme);

      if (toggle) {
        toggle.addEventListener('click', function () {
          const next = currentTheme() === 'dark' ? 'light' : 'dark';
          apply(next);
          try {
            window.localStorage.setItem(STORAGE_KEY, next);
          } catch (error) {
            /* تجاهل: التخزين غير متاح */
          }
          Toast.show(next === 'dark' ? 'تم تفعيل الوضع الليلي' : 'تم تفعيل الوضع النهاري');
        });
      }
    }

    return { init, apply, currentTheme };
  })();


  /* ===========================================================================
     05. التنبيهات المنبثقة (Toast)
     =========================================================================== */

  const Toast = (function () {
    let box = null;

    function ensure() {
      if (!box) {
        box = document.createElement('div');
        box.className = 'toast-stack';
        box.setAttribute('role', 'status');
        box.setAttribute('aria-live', 'polite');
        document.body.appendChild(box);
      }
      return box;
    }

    function show(message, duration) {
      const host = ensure();
      const toast = document.createElement('div');
      toast.className = 'toast';
      toast.textContent = message;
      host.appendChild(toast);

      window.requestAnimationFrame(function () {
        toast.classList.add('is-visible');
      });

      window.setTimeout(function () {
        toast.classList.remove('is-visible');
        window.setTimeout(function () {
          if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 350);
      }, duration || 2600);
    }

    return { show };
  })();


  /* ===========================================================================
     06. قائمة الجوال
     =========================================================================== */

  const MobileNav = (function () {
    const nav = $('#primaryNav');
    const toggle = $('#navToggle');
    const overlay = $('#navOverlay');
    let lastFocused = null;

    function isOpen() {
      return nav && nav.classList.contains('is-open');
    }

    function open() {
      if (!nav || !toggle) return;
      lastFocused = document.activeElement;
      nav.classList.add('is-open');
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'إغلاق القائمة');
      document.body.style.overflow = 'hidden';

      if (overlay) {
        overlay.hidden = false;
        window.requestAnimationFrame(function () {
          overlay.classList.add('is-visible');
        });
      }

      const firstLink = $('.nav__link', nav);
      if (firstLink) firstLink.focus();
    }

    function close() {
      if (!nav || !toggle) return;
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'فتح القائمة');
      document.body.style.overflow = '';

      if (overlay) {
        overlay.classList.remove('is-visible');
        window.setTimeout(function () {
          overlay.hidden = true;
        }, 300);
      }

      if (lastFocused && typeof lastFocused.focus === 'function') {
        lastFocused.focus();
      }
    }

    function init() {
      if (toggle) toggle.addEventListener('click', function () {
        if (isOpen()) close(); else open();
      });
      if (overlay) overlay.addEventListener('click', close);

      $$('.nav__link', nav).forEach(function (link) {
        link.addEventListener('click', function () {
          if (isOpen()) window.setTimeout(close, 120);
        });
      });

      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen()) close();
      });

      window.addEventListener('resize', function () {
        if (window.innerWidth > 900 && isOpen()) close();
      });
    }

    return { init, open, close, isOpen };
  })();


  /* ===========================================================================
     07. التمرير السلس بين الأقسام
     =========================================================================== */

  const SmoothScroll = (function () {
    function headerOffset() {
      const header = $('#siteHeader');
      return header ? header.offsetHeight + 12 : 80;
    }

    function scrollToTarget(target) {
      if (!target) return;

      const offset = headerOffset();
      const top = target.getBoundingClientRect().top + window.pageYOffset - offset;

      window.scrollTo({
        top: Math.max(0, top),
        behavior: prefersReducedMotion.matches ? 'auto' : 'smooth'
      });

      const id = target.getAttribute('id');
      if (id) {
        $$('.nav__link').forEach(function (link) {
          link.classList.toggle('is-active', link.getAttribute('href') === '#' + id);
        });
        NavIndicator.update();
      }
    }

    function init() {
      $$('a[href^="#"]').forEach(function (link) {
        link.addEventListener('click', function (event) {
          const href = link.getAttribute('href');
          if (!href || href === '#') return;

          const target = document.getElementById(href.slice(1));
          if (!target) return;

          event.preventDefault();
          scrollToTarget(target);

          if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', href);
          }
        });
      });
    }

    return { init, scrollToTarget };
  })();


  /* ===========================================================================
     08. شريط تقدم القراءة
     =========================================================================== */

  const ReadingProgress = (function () {
    const bar = $('#readingProgress');
    const container = $('.reading-progress');
    let lastPercent = -1;

    const update = throttleRaf(function () {
      if (!bar) return;

      const doc = document.documentElement;
      const scrollTop = window.pageYOffset || doc.scrollTop;
      const scrollable = doc.scrollHeight - window.innerHeight;
      const percent = scrollable > 0 ? Math.min(100, Math.max(0, (scrollTop / scrollable) * 100)) : 0;

      bar.style.width = percent.toFixed(2) + '%';

      if (container) {
        container.setAttribute('aria-valuenow', Math.round(percent));
      }

      lastPercent = percent;
      return percent;
    });

    function init() {
      window.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update, { passive: true });
      update();
    }

    return { init, update, get percent() { return lastPercent; } };
  })();


  /* ===========================================================================
     09. تحديد القسم النشط + مؤشر شريط التنقل
     =========================================================================== */

  const NavIndicator = (function () {
    const nav = $('#primaryNav');
    const indicator = $('#navIndicator');
    const navList = $('.nav__list', nav);

    function move() {
      if (!nav || !indicator) return;

      const active = $('.nav__link.is-active', nav);
      if (!active) {
        indicator.style.opacity = '0';
        return;
      }

      const isRTL = window.getComputedStyle(nav).direction === 'rtl';
      const width = active.offsetWidth;
      const offset = active.offsetLeft;

      indicator.style.width = width + 'px';
      indicator.style.opacity = '1';

      if (isRTL) {
        indicator.style.right = (navList.offsetWidth - offset - width) + 'px';
        indicator.style.left = 'auto';
      } else {
        indicator.style.left = offset + 'px';
        indicator.style.right = 'auto';
      }
    }

    const update = throttleRaf(move);

    function init() {
      window.addEventListener('resize', update, { passive: true });
      window.addEventListener('load', update);
      window.setTimeout(update, 300);
      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(update).catch(function () {});
      }
    }

    return { init, update };
  })();

  const ScrollSpy = (function () {
    let sections = [];

    function collect() {
      sections = $$('.nav__link')
        .map(function (link) {
          const id = (link.getAttribute('href') || '').slice(1);
          const section = id ? document.getElementById(id) : null;
          return section ? { link: link, section: section } : null;
        })
        .filter(Boolean);
    }

    function update() {
      if (!sections.length) return;

      const header = $('#siteHeader');
      const offset = (header ? header.offsetHeight : 70) + 40;
      const scrollPos = window.pageYOffset + offset;

      const atBottom = (window.innerHeight + window.pageYOffset) >= (document.documentElement.scrollHeight - 4);

      let current = sections[0];
      for (let i = 0; i < sections.length; i += 1) {
        if (sections[i].section.offsetTop <= scrollPos) {
          current = sections[i];
        }
      }
      if (atBottom) current = sections[sections.length - 1];

      sections.forEach(function (item) {
        item.link.classList.toggle('is-active', item.link === current.link);
      });

      NavIndicator.update();
    }

    const throttled = throttleRaf(update);

    function init() {
      collect();
      window.addEventListener('scroll', throttled, { passive: true });
      window.addEventListener('resize', throttled, { passive: true });
      throttled();
    }

    return { init, update };
  })();


  /* ===========================================================================
     10. حركات الظهور عند التمرير (IntersectionObserver)
     =========================================================================== */

  const Reveal = (function () {
    function showAll() {
      $$('.reveal').forEach(function (element) {
        element.classList.add('is-visible');
      });
    }

    function init() {
      const items = $$('.reveal');

      if (STATIC_MODE || prefersReducedMotion.matches || !('IntersectionObserver' in window)) {
        showAll();
        return;
      }

      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          const element = entry.target;
          const delay = parseInt(element.getAttribute('data-delay') || '0', 10);
          element.style.setProperty('--reveal-delay', (delay * 110) + 'ms');
          element.classList.add('is-visible');
          observer.unobserve(element);
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

      items.forEach(function (element) {
        observer.observe(element);
      });
    }

    return { init, showAll };
  })();


  /* ===========================================================================
     11. تأثير الكتابة المتحرك
     =========================================================================== */

  const TypingEffect = (function () {
    const target = $('#typedRole');
    const caret = $('#typedCaret');
    if (!target) return { init: function () {}, setLanguage: function () {} };

    let language = 'ar';
    let started = false;
    let token = 0;

    async function run(currentToken) {
      if (prefersReducedMotion.matches) {
        target.textContent = (ROLES[language] || ROLES.ar).map((s) => s.text).join('');
        return;
      }

      const segments = ROLES[language] || ROLES.ar;

      for (let s = 0; s < segments.length; s += 1) {
        const segment = segments[s];
        const characters = Array.from(segment.text);

        for (let i = 0; i < characters.length; i += 1) {
          if (currentToken !== token) return; // أُلغيت التشغيل (تبديل اللغة)
          target.textContent += characters[i];
          await delay(segment.speed + (i % 3 === 0 ? 26 : 0));
        }

        if (currentToken !== token) return;
        await delay(segment.pause);
      }
    }

    /** بدء (أو إعادة بدء) الحركة ب token جديد يُبطل أي تشغيل سابق. */
    function start(wait) {
      const currentToken = ++token;
      target.textContent = '';
      window.setTimeout(function () {
        run(currentToken);
      }, wait);
    }

    function setLanguage(lang) {
      language = lang;
      if (!started) return; // لم تبدأ الحركة بعد — ستبدأ تلقائيًا باللغة الحالية

      if (STATIC_MODE) {
        target.textContent = (ROLES[language] || ROLES.ar).map((s) => s.text).join('');
        return;
      }

      start(220);
    }

    function init() {
      if (started) return;
      started = true;

      // في الوضع الساكن: عرض النص النهائي مباشرة
      if (STATIC_MODE) {
        target.textContent = (ROLES[language] || ROLES.ar).map((s) => s.text).join('');
        return;
      }

      start(700);
    }

    return { init, setLanguage };
  })();


  /* ===========================================================================
     12أ. المشهد ثلاثي الأبعاد — Parallax خفيف مع حركة المؤشر
     -----------------------------------------------------------------------
     يحرّك طبقة العناصر حسب موضع المؤشر لإضافة عمق بصري هادئ.
     =========================================================================== */

  const SceneParallax = (function () {
    const scene = $('#scene');
    const objects = $('#sceneObjects');
    if (!scene || !objects) return { init: function () {} };

    const MAX_SHIFT = 16;   // أقصى إزاحة بالبكسل
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let running = false;

    function render() {
      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;

      objects.style.transform =
        'translate3d(' + currentX.toFixed(2) + 'px,' + currentY.toFixed(2) + 'px,0)';

      if (Math.abs(targetX - currentX) > 0.1 || Math.abs(targetY - currentY) > 0.1) {
        window.requestAnimationFrame(render);
      } else {
        running = false;
      }
    }

    function start() {
      if (running) return;
      running = true;
      window.requestAnimationFrame(render);
    }

    function onMove(event) {
      const rect = scene.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;

      targetX = -x * MAX_SHIFT;
      targetY = -y * MAX_SHIFT;
      start();
    }

    function reset() {
      targetX = 0;
      targetY = 0;
      start();
    }

    function init() {
      // تحويل خصائص البيانات إلى متغيّرات CSS (العمق ونسبة الطفو)
      $$('.obj').forEach(function (object) {
        const depth = object.getAttribute('data-depth');
        const float = object.getAttribute('data-float');
        if (depth) object.style.setProperty('--depth', depth);
        if (float) object.style.setProperty('--float', float);
      });

      if (prefersReducedMotion.matches || !canHover.matches) return;

      const hero = $('.hero');
      if (!hero) return;

      hero.addEventListener('mousemove', onMove);
      hero.addEventListener('mouseleave', reset);
    }

    return { init };
  })();


  /* ===========================================================================
     13. تأثيرات البطاقات التفاعلية (Tilt + لمعة)
     =========================================================================== */

  const CardEffects = (function () {
    const MAX_TILT = 7;

    function attachTilt() {
      if (!canHover.matches || prefersReducedMotion.matches) return;

      $$('[data-tilt]').forEach(function (card) {
        if (card.dataset.tiltBound === '1') return;
        card.dataset.tiltBound = '1';

        let rafId = null;

        function onMove(event) {
          const rect = card.getBoundingClientRect();
          const x = (event.clientX - rect.left) / rect.width;
          const y = (event.clientY - rect.top) / rect.height;

          if (rafId) return;
          rafId = window.requestAnimationFrame(function () {
            const rotateY = (x - 0.5) * MAX_TILT * 2;
            const rotateX = (0.5 - y) * MAX_TILT * 2;
            const lift = card.classList.contains('project--flip') ? 0 : -6;

            card.style.transform =
              'perspective(900px) rotateX(' + rotateX.toFixed(2) + 'deg) rotateY(' +
              rotateY.toFixed(2) + 'deg) translateY(' + lift + 'px)';

            card.style.setProperty('--pointer-x', (x * 100).toFixed(1) + '%');
            card.style.setProperty('--pointer-y', (y * 100).toFixed(1) + '%');
            rafId = null;
          });
        }

        function onLeave() {
          if (rafId) {
            window.cancelAnimationFrame(rafId);
            rafId = null;
          }
          card.style.transform = '';
        }

        card.addEventListener('mousemove', onMove);
        card.addEventListener('mouseleave', onLeave);
      });
    }

    function pulse(element) {
      if (!element) return;
      element.classList.remove('is-pulsing');
      void element.offsetWidth;
      element.classList.add('is-pulsing');
      window.setTimeout(function () {
        element.classList.remove('is-pulsing');
      }, 1200);
    }

    function init() {
      attachTilt();
      if (typeof canHover.addEventListener === 'function') {
        canHover.addEventListener('change', attachTilt);
      }
    }

    return { init, pulse };
  })();


  /* ===========================================================================
     13. زر العودة إلى أعلى الصفحة
     =========================================================================== */

  const BackToTop = (function () {
    const button = $('#backToTop');
    const ring = $('#backToTopProgress');
    if (!button) return { init: function () {} };

    function update() {
      const percent = ReadingProgress.percent || 0;
      const visible = window.pageYOffset > 420;

      button.classList.toggle('is-visible', visible);
      if (ring) ring.style.setProperty('--progress', percent.toFixed(1));
    }

    function init() {
      window.addEventListener('scroll', throttleRaf(update), { passive: true });
      window.addEventListener('resize', throttleRaf(update), { passive: true });

      button.addEventListener('click', function () {
        window.scrollTo({
          top: 0,
          behavior: prefersReducedMotion.matches ? 'auto' : 'smooth'
        });
      });

      update();
    }

    return { init };
  })();


  /* ===========================================================================
     14. نافذة تفاصيل المشروع (Modal)
     =========================================================================== */

  const ProjectModal = (function () {
    const modal = $('#projectModal');
    const dialog = $('.modal__dialog', modal);
    const closeBtn = $('#modalClose');
    const image = $('#modalImage');
    const title = $('#modalTitle');
    const category = $('#modalCategory');
    const content = $('#modalContent');
    let lastFocused = null;

    function open(projectNumber) {
      const card = $('.project[data-project="' + projectNumber + '"]');
      if (!card || !modal) return;

      const cardTitle = $('.project__title', card);
      const cardCategory = $('.project__category', card);
      const cardImage = $('.project__media img', card);
      const detail = $('.project__detail', card);

      if (cardTitle) title.textContent = cardTitle.textContent.trim();
      if (cardCategory) category.textContent = cardCategory.textContent.trim();

      if (cardImage) {
        image.src = cardImage.getAttribute('src');
        image.alt = cardImage.getAttribute('alt') || '';
      }

      content.innerHTML = '';
      if (detail) {
        const clone = detail.cloneNode(true);
        clone.removeAttribute('hidden');
        while (clone.firstChild) {
          content.appendChild(clone.firstChild);
        }
      }

      lastFocused = document.activeElement;
      modal.hidden = false;
      document.body.style.overflow = 'hidden';

      if (closeBtn) closeBtn.focus();
    }

    function close() {
      if (!modal || modal.hidden) return;
      modal.hidden = true;
      document.body.style.overflow = '';

      if (lastFocused && typeof lastFocused.focus === 'function') {
        lastFocused.focus();
      }
    }

    function trapFocus(event) {
      if (!modal || modal.hidden || event.key !== 'Tab') return;

      const focusables = $$('a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])', dialog)
        .filter(function (element) { return element.offsetParent !== null; });

      if (!focusables.length) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    function init() {
      if (!modal) return;

      $$('[data-open-project]').forEach(function (button) {
        button.addEventListener('click', function () {
          open(button.getAttribute('data-open-project'));
        });
      });

      if (closeBtn) closeBtn.addEventListener('click', close);

      $$('[data-close-modal]', modal).forEach(function (element) {
        element.addEventListener('click', close);
      });

      document.addEventListener('keydown', function (event) {
        if (modal.hidden) return;
        if (event.key === 'Escape') close();
        trapFocus(event);
      });
    }

    return { init, open, close };
  })();


  /* ===========================================================================
     15. الطباعة وتصدير PDF
     -----------------------------------------------------------------------
     يفتح نافذة الطباعة القياسية في المتصفح، ومن ثم يمكن اختيار
     "حفظ بصيغة PDF" للحصول على ملف جاهز للطباعة أو المشاركة.
     =========================================================================== */

  const PrintCV = (function () {
    const button = $('#printCv');

    function init() {
      if (!button) return;

      button.addEventListener('click', function () {
        Reveal.showAll();

        Toast.show(
          I18n.current === 'ar'
            ? 'اختر «حفظ بصيغة PDF» من نافذة الطباعة لحفظ السيرة'
            : 'Choose “Save as PDF” in the print dialog to save the CV',
          4200
        );

        window.setTimeout(function () {
          window.print();
        }, 260);
      });

      window.addEventListener('beforeprint', function () {
        document.documentElement.setAttribute('data-printing', 'true');
      });
      window.addEventListener('afterprint', function () {
        document.documentElement.removeAttribute('data-printing');
      });
    }

    return { init };
  })();


  /* ===========================================================================
     16. سنة التذييل + حالة الرأس
     =========================================================================== */

  const HeaderState = (function () {
    const header = $('#siteHeader');

    function update() {
      if (!header) return;
      header.classList.toggle('is-scrolled', window.pageYOffset > 40);
    }

    function init() {
      window.addEventListener('scroll', throttleRaf(update), { passive: true });
      update();
    }

    return { init };
  })();

  const FooterYear = (function () {
    function init() {
      const year = $('#currentYear');
      if (year) year.textContent = String(new Date().getFullYear());
    }
    return { init };
  })();


  /* ===========================================================================
     17. تفضيل تقليل الحركة
     =========================================================================== */

  const ReducedMotion = (function () {
    function apply() {
      if (prefersReducedMotion.matches) {
        document.documentElement.classList.add('reduce-motion');
        Reveal.showAll();
      } else {
        document.documentElement.classList.remove('reduce-motion');
      }
    }

    function init() {
      apply();
      if (typeof prefersReducedMotion.addEventListener === 'function') {
        prefersReducedMotion.addEventListener('change', apply);
      }
    }

    return { init };
  })();


  /* ===========================================================================
     18. تهيئة الصفحة
     =========================================================================== */

  function init() {
    I18n.init();
    ThemeManager.init();
    MobileNav.init();
    SmoothScroll.init();
    ReadingProgress.init();
    NavIndicator.init();
    ScrollSpy.init();
    Reveal.init();
    TypingEffect.init();
    SceneParallax.init();
    CardEffects.init();
    BackToTop.init();
    ProjectModal.init();
    PrintCV.init();
    ReducedMotion.init();
    HeaderState.init();
    FooterYear.init();

    $$('.project img, .portrait img, .about__visual img').forEach(function (image) {
      image.setAttribute('draggable', 'false');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
