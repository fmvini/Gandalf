'use client'

// Adapted from Cult UI's 3D Carousel, published on 21st.dev.
// MIT: see frontend/THIRD_PARTY_NOTICES.md. Uses a bounded coverflow instead of
// the upstream cylinder/modal, with explicit navigation and reduced motion.
import { useState, type KeyboardEvent } from 'react'
import { motion, useMotionValue, useReducedMotion } from 'motion/react'
import { ArrowLeft, ArrowRight, ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { showcaseBooks } from '../../lib/showcase'

export function BookCarousel() {
  const [active, setActive] = useState(0)
  const reduced = useReducedMotion()
  const dragX = useMotionValue(0)
  const book = showcaseBooks[active]
  function move(direction: number) {
    setActive(current => (current + direction + showcaseBooks.length) % showcaseBooks.length)
  }
  function onKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
    event.preventDefault()
    move(event.key === 'ArrowRight' ? 1 : -1)
  }

  return <section className="book-showcase" aria-label="Explore livros do catálogo" aria-roledescription="carrossel" onKeyDown={onKeyDown}>
    <div className="showcase-top"><span>Na sua próxima página</span><span>Catálogo Gandalf</span></div>
    <div className="cover-stage">
      <motion.div className="cover-track" drag={reduced ? false : 'x'} dragConstraints={{ left: 0, right: 0 }} dragElastic={0.08} style={{ x: dragX }} onDragEnd={(_, info) => {
        if (Math.abs(info.offset.x) > 45) move(info.offset.x < 0 ? 1 : -1)
      }}>
        {showcaseBooks.map((item, index) => {
          let offset = (index - active + showcaseBooks.length) % showcaseBooks.length
          if (offset > showcaseBooks.length / 2) offset -= showcaseBooks.length
          return <motion.div className="showcase-cover" key={item.title} aria-hidden={index !== active} initial={reduced ? false : { x: 0, z: -120, rotateY: 0, scale: 0.85, opacity: 0.75 }}
            animate={{ x: offset * 128, z: -Math.abs(offset) * 90, rotateY: offset * -24, scale: offset === 0 ? 1 : 0.87, opacity: offset === 0 ? 1 : 0.65 }}
            transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 180, damping: 26 }}
            style={{ zIndex: 3 - Math.abs(offset) }}>
            <img src={item.cover} alt={'Capa de ' + item.title + ', edição em inglês'} draggable={false} width="220" height="320" fetchPriority={index === 0 ? 'high' : 'auto'} />
          </motion.div>
        })}
      </motion.div>
    </div>
    <div className="showcase-details">
      <div aria-live="polite" aria-atomic="true" className="showcase-current">
        <motion.div key={book.title} initial={reduced ? false : { opacity: 0.7, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.22 }}><p>{book.mood}</p><h2>{book.title}</h2><span>{book.author}</span></motion.div>
      </div>
      <div className="carousel-controls">
        <button className="icon-button" type="button" onClick={() => move(-1)} aria-label="Livro anterior"><ArrowLeft size={18} /></button>
        <span aria-hidden="true">{active + 1} / {showcaseBooks.length}</span>
        <button className="icon-button" type="button" onClick={() => move(1)} aria-label="Próximo livro"><ArrowRight size={18} /></button>
      </div>
    </div>
    <Link className="showcase-link" to="/read-with-music" state={{ query: book.title }}>Encontrar a trilha deste livro <ArrowUpRight size={17} /></Link>
  </section>
}
