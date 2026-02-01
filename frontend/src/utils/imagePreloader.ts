/**
 * Image Preloader Utility
 * Preloads critical images to improve user experience
 */

// List of all images to preload
const IMAGES_TO_PRELOAD = [
  // Favicon
  '/hypnos.webp',
  
  // Ad banners (landing page carousel)
  '/ads/pub1_focaccia.webp',
  '/ads/pub2_risotto.webp',
  '/ads/pub3_vieux.webp',
  '/ads/pub4_exotint.webp',
  '/ads/pub5_shotgun.webp',
  
  // Supplement banners
  '/images/BiereAbsinthe.webp',
  '/images/PouletRoti.webp',
]

/**
 * Preload images by creating Image objects
 * This triggers the browser to download and cache images
 */
export const preloadImages = (): void => {
  IMAGES_TO_PRELOAD.forEach(src => {
    const img = new Image()
    img.src = src
  })
}

/**
 * Preload images with Promise support for tracking completion
 * @returns Promise that resolves when all images are loaded
 */
export const preloadImagesAsync = (): Promise<void[]> => {
  const promises = IMAGES_TO_PRELOAD.map(src => {
    return new Promise<void>((resolve) => {
      const img = new Image()
      img.onload = () => resolve()
      img.onerror = () => {
        console.warn(`Failed to preload image: ${src}`)
        resolve() // Still resolve to not block other images
      }
      img.src = src
    })
  })
  
  return Promise.all(promises)
}
