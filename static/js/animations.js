/**
 * KUBERA BANK – Cinematic Bank Entrance Animation
 * Built with GSAP & ScrollTrigger
 * 
 * Experience Flow:
 * 1. Intro Reveal: Logo & Tagline emerge smoothly on initial load.
 * 2. Majestic Hero Display: Grand Neoclassical Bank Facade + Visible Headings & CTAs.
 * 3. Entering the Bank:
 *    - User scrolls: Hero text glides upward.
 *    - Camera pushes inward, zooming straight toward the grand portico.
 *    - Massive 3D Brass & Glass doors swing wide open.
 *    - Interior grand atrium illuminates with warm golden chandeliers.
 *    - Welcome concierge card reveals inside the bank.
 *    - Smooth flow into banking services.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. INTRO LOADER ANIMATION
    // ==========================================
    const introLoader = document.getElementById('introLoader');
    const introLogo   = introLoader?.querySelector('.kb-intro-logo');
    const introTag    = introLoader?.querySelector('.kb-intro-tagline');
    const introBar    = introLoader?.querySelector('.kb-intro-bar');

    if (introLoader && window.gsap) {
        const introTL = gsap.timeline({
            onComplete: () => {
                initBankEntranceExperience();
            }
        });

        introTL.to(introLogo, {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: 'power2.out'
        }, 0.2);

        introTL.to(introTag, {
            opacity: 1,
            duration: 0.5,
            ease: 'power2.out'
        }, 0.7);

        introTL.to(introBar, {
            opacity: 1,
            duration: 0.3
        }, 0.8);

        // Slide away the splash loader
        introTL.to(introLoader, {
            yPercent: -100,
            duration: 0.75,
            ease: 'power3.inOut',
            delay: 1.1
        });
    } else {
        if (introLoader) introLoader.style.display = 'none';
        initBankEntranceExperience();
    }


    // ==========================================
    // 2. THE GRAND BANK ENTRANCE SCROLL EXPERIENCE
    // ==========================================
    function initBankEntranceExperience() {
        const heroSection   = document.querySelector('.kb-hero');
        const heroContent   = document.getElementById('heroContent');
        const sceneBuilding = document.getElementById('sceneBuilding');
        const doorLeft      = document.getElementById('doorLeft');
        const doorRight     = document.getElementById('doorRight');

        if (!heroSection || !sceneBuilding || !window.gsap) return;

        // Register ScrollTrigger plugin
        if (window.ScrollTrigger) {
            gsap.registerPlugin(ScrollTrigger);
        } else {
            return;
        }

        // Set initial visible states
        gsap.set(heroContent, { opacity: 1, y: 0 });
        gsap.set(sceneBuilding, { scale: 1, y: 0, opacity: 1, transformOrigin: 'center 85%' });
        gsap.set(doorLeft, { rotateY: 0 });
        gsap.set(doorRight, { rotateY: 0 });

        // CREATE PINNED SCROLL TIMELINE
        const entranceTL = gsap.timeline({
            scrollTrigger: {
                trigger: heroSection,
                start: 'top top',
                end: '+=1000',       // 1000px of smooth cinematic entrance scroll
                scrub: 1.0,          // Ultra-smooth interpolation
                pin: true,           // Pin the screen during entrance
                anticipatePin: 1
            }
        });

        // STEP 1: Hero text & CTAs fade up and dissolve as you start moving
        entranceTL.to(heroContent, {
            opacity: 0,
            y: -60,
            scale: 0.98,
            duration: 0.25,
            ease: 'power1.in'
        }, 0);

        // STEP 2: Camera pushes forward towards the bank portico
        entranceTL.to(sceneBuilding, {
            scale: 2.7,
            y: '-14%',
            duration: 0.8,
            ease: 'power1.inOut'
        }, 0.1);

        // STEP 3: Grand 3D Brass & Glass Doors swing open in perspective
        entranceTL.to(doorLeft, {
            rotateY: -85,
            duration: 0.5,
            ease: 'power2.out',
            transformStyle: 'preserve-3d'
        }, 0.35);

        entranceTL.to(doorRight, {
            rotateY: 85,
            duration: 0.5,
            ease: 'power2.out',
            transformStyle: 'preserve-3d'
        }, 0.35);

        // STEP 4: As you step through, facade smoothly dissolves into the Banking Hall
        entranceTL.to(sceneBuilding, {
            opacity: 0.3,
            scale: 3.4,
            duration: 0.4,
            ease: 'power1.in'
        }, 0.7);
    }


    // ==========================================
    // 3. SECTION SCROLL ANIMATIONS (Below Hero)
    // ==========================================
    if (window.gsap && window.ScrollTrigger) {
        // Animate Service Cards
        gsap.utils.toArray('.kb-service-card').forEach((card, i) => {
            gsap.from(card, {
                scrollTrigger: {
                    trigger: card,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                },
                y: 35,
                opacity: 0,
                duration: 0.6,
                delay: (i % 3) * 0.1,
                ease: 'power2.out'
            });
        });

        // Animate Products & Cards
        gsap.utils.toArray('.kb-product-card, .kb-cc-card').forEach((card, i) => {
            gsap.from(card, {
                scrollTrigger: {
                    trigger: card,
                    start: 'top 88%',
                    toggleActions: 'play none none none'
                },
                y: 30,
                opacity: 0,
                duration: 0.55,
                delay: (i % 3) * 0.1,
                ease: 'power2.out'
            });
        });

        // Animate Statistics in About Section
        gsap.utils.toArray('.kb-stat-card').forEach((stat, i) => {
            gsap.from(stat, {
                scrollTrigger: {
                    trigger: stat,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                },
                scale: 0.9,
                opacity: 0,
                duration: 0.5,
                delay: i * 0.08,
                ease: 'back.out(1.5)'
            });
        });
    }


    // ==========================================
    // 4. SMOOTH SCROLL FOR ANCHOR LINKS
    // ==========================================
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Scroll guide click to step into bank
    const scrollGuide = document.getElementById('scrollGuide');
    scrollGuide?.addEventListener('click', () => {
        window.scrollBy({ top: 600, behavior: 'smooth' });
    });

});
