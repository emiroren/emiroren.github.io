// Dil verileri
const translations = {
  tr: {
    nav: ["Hakkımda", "Projeler", "Sertifikalar"],
    aboutTitle: "Hakkımda",
    aboutDesc: "Ben İbrahim Emir Ören, Denizli Necla Ergun Abalıoğlu Ticaret Mesleki ve Teknik Anadolu Lisesi'nde 12. sınıf öğrencisiyim. Web geliştirme alanında projeler üreten, HTML, CSS, JavaScript ve PHP konularında bilgi sahibi bir lise öğrencisiyim. Kullanıcı deneyimini ön planda tutan, modern ve responsıve tasarımlar oluşturmayı hedefliyor; sürekli olarak kendimi geliştirmeye çalışıyorum.",
    contact: [
      { label: "E-posta", value: "emiroren.business@gmail.com" },
      { label: "GitHub", value: "<a target='_blank' href='https://github.com/emiroren'>github.com/emiroren</a>" }
    ],
    projectsTitle: "Projelerim",
    certificatesTitle: "Sertifikalarım",
    footer: "&copy; 2025 İbrahim Emir Ören"
  },
  en: {
    nav: ["About", "Projects", "Certificates"],
    aboutTitle: "About Me",
    aboutDesc: "My name is İbrahim Emir Ören, and I am a 12th grade student at Denizli Necla Ergun Abalıoğlu Trade Vocational and Technical Anatolian High School. I am a high school student who produces projects in the field of web development and has knowledge of HTML, CSS, JavaScript, and PHP. I aim to create modern and responsive designs that prioritise user experience, and I constantly strive to improve myself.",
    contact: [
      { label: "Email", value: "emiroren.business@gmail.com" },
      { label: "GitHub", value: "<a target='_blank' href='https://github.com/emiroren'>github.com/emiroren</a>" }
    ],
    projectsTitle: "My Projects",
    certificatesTitle: "My Certificates",
    footer: "&copy; 2025 İbrahim Emir Ören"
  }
};

// Projeler ve sertifikalar iki dilde
const projectsData = {
  tr: [
    {
      title: "Sosyal Medya Uzmanlığı Satışı",
      description: "Sosyal medya uzmanlığı hizmeti sunan,bir web sitesi tasarladım. <br> <br> Kullanıcının: <br> -Fiyat bilgisine erişebilmesi <br> -Eğitim içeriğini görebilmesi",
      link: "/proje-1/proje1.html"
    },
    {
      title: "Otel Tanıtımı",
      description: "Müşterinin otel hakkında bilgi alabileceği,resimlerini,oda seçeneklerini ve herhangi bir sorunda müşteri hizmetlerine ulaşabilecekleri bir form tasarladım. <br> <br> Kullanıcının: <br> -Otel hakkında bilgi sahibi olabilmesi <br> -Otelin manzarasını görebilmesi <br> -Oda çeşitlerini görebilmesi <br> -Rezervasyon yaptırma imkanına sahip olması",
      link: "/proje-2/proje2.html"
    },
    {
      title: "Blog Sitesi",
      description: "Bu projede Kişisel blog sitesi tasarladım. <br> <br> Kullanıcının: <br> -Blog yazılarını okuyabilmesi <br> -Yeni yazıları takip edebilmesi",
      link: "/proje-3/index.html"
    }
  ],
  en: [
    {
      title: "Sample Project 1",
      description: "In this project, I did the following...",
      link: "/proje-1/proje1.html"
    },
    {
      title: "Sample Project 2",
      description: "In this project, I accomplished the following...",
      link: "/proje-2/proje2.html"
    }
  ]
};
const certificatesData = {
  tr: [
    {
      title: "Enerjinle Gelecek Senin Projesi",
      description: "Katılım Belgesi",
      img: "./assets/aydem-katilim-belgesi.jpg"
    }
  ],
  en: [
    {
      title: "Enerjinle Gelecek Senin Project",
      description: "Certificate of Participation",
      img: "./assets/aydem-katilim-belgesi.jpg"
    }
  ]
};

let currentLang = 'tr';

function setLanguage(lang) {
  currentLang = lang;
  // Menü
  const navLinks = document.querySelectorAll('nav a');
  translations[lang].nav.forEach((text, i) => {
    navLinks[i].textContent = text;
  });
  // Hakkımda başlık ve açıklama
  document.querySelector('#about h2').textContent = translations[lang].aboutTitle;
  document.querySelector('#about .about-info p').textContent = translations[lang].aboutDesc;
  // İletişim
  const contactList = document.querySelector('.contact-list');
  contactList.innerHTML = '';
  translations[lang].contact.forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${item.label}:</strong> ${item.value}`;
    contactList.appendChild(li);
  });
  // Projeler başlığı
  document.querySelector('#projects h2').textContent = translations[lang].projectsTitle;
  // Sertifikalar başlığı
  document.querySelector('#certificates h2').textContent = translations[lang].certificatesTitle;
  // Footer
  document.querySelector('footer .container p').innerHTML = translations[lang].footer;
  // Projeler ve sertifikalar
  renderProjects();
  renderCertificates();
  // Buton aktifliği
  document.getElementById('lang-tr').classList.toggle('active', lang === 'tr');
  document.getElementById('lang-en').classList.toggle('active', lang === 'en');
}

function renderProjects() {
  const list = document.getElementById('projects-list');
  list.innerHTML = '';
  projectsData[currentLang].forEach(proj => {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <div class="project-title">${proj.title}</div>
      <div class="project-desc">${proj.description}</div>
      ${proj.link ? `<a class="project-link" href="${proj.link}" target="_blank">${currentLang === 'tr' ? 'Projeye Git' : 'View Project'}</a>` : ''}
    `;
    list.appendChild(card);
  });
}

function renderCertificates() {
  const list = document.getElementById('certificates-list');
  list.innerHTML = '';
  certificatesData[currentLang].forEach(cert => {
    const card = document.createElement('div');
    card.className = 'certificate-card';
    card.innerHTML = `
      ${cert.img ? `<img class="certificate-img" src="${cert.img}" alt="${cert.title}">` : ''}
      <div class="project-title">${cert.title}</div>
      <div class="project-desc">${cert.description}</div>
    `;
    // Sertifika fotoğrafına tıklama olayı ekle
    if (cert.img) {
      card.querySelector('.certificate-img').addEventListener('click', function() {
        openCertificateModal(cert.img);
      });
    }
    list.appendChild(card);
  });
}

// Modal açma ve kapama fonksiyonları
function openCertificateModal(imgSrc) {
  const modal = document.getElementById('certificate-modal');
  const modalImg = document.getElementById('modal-img');
  modalImg.src = imgSrc;
  modal.style.display = 'flex';
}

document.getElementById('modal-close').onclick = function() {
  document.getElementById('certificate-modal').style.display = 'none';
};
document.getElementById('certificate-modal').onclick = function(e) {
  if (e.target === this) {
    this.style.display = 'none';
  }
};

document.getElementById('lang-tr').onclick = function() { setLanguage('tr'); };
document.getElementById('lang-en').onclick = function() { setLanguage('en'); };

// Sürekli tekrar eden basit typewriter efekti
(function typewriterLoop() {
  const text = 'İbrahim Emir Ören';
  const el = document.getElementById('typewriter');
  let i = 0;
  let isDeleting = false;

  function type() {
    if (!el) return;
    if (!isDeleting) {
      el.textContent = text.slice(0, i + 1);
      i++;
      if (i === text.length) {
        setTimeout(() => { isDeleting = true; type(); }, 1200);
        return;
      }
    } else {
      el.textContent = text.slice(0, i - 1);
      i--;
      if (i === 0) {
        isDeleting = false;
      }
    }
    setTimeout(type, isDeleting ? 60 : 110);
  }
  type();
})();

document.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang);
}); 