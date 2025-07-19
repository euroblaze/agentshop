import React from 'react';
import { NavLink } from 'react-router-dom';

export const ShopFooter: React.FC = () => {
  const footerSections = [
    {
      title: 'Products',
      links: [
        { name: 'All Products', href: '/products' },
        { name: 'Categories', href: '/categories' },
        { name: 'New Arrivals', href: '/products?filter=new' },
        { name: 'Best Sellers', href: '/products?filter=popular' }
      ]
    },
    {
      title: 'Support',
      links: [
        { name: 'Help Center', href: '/help' },
        { name: 'Contact Us', href: '/contact' },
        { name: 'FAQ', href: '/faq' },
        { name: 'Returns', href: '/returns' }
      ]
    },
    {
      title: 'Company',
      links: [
        { name: 'About Us', href: '/about' },
        { name: 'Careers', href: '/careers' },
        { name: 'Blog', href: '/blog' },
        { name: 'Press', href: '/press' }
      ]
    },
    {
      title: 'Legal',
      links: [
        { name: 'Privacy Policy', href: '/privacy' },
        { name: 'Terms of Service', href: '/terms' },
        { name: 'Cookie Policy', href: '/cookies' },
        { name: 'GDPR', href: '/gdpr' }
      ]
    }
  ];

  const socialLinks = [
    {
      name: 'Twitter',
      href: '#',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
        </svg>
      )
    },
    {
      name: 'Facebook',
      href: '#',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
        </svg>
      )
    },
    {
      name: 'Instagram',
      href: '#',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" d="M12.017 0C8.396 0 7.955.013 6.729.078 5.505.144 4.668.334 3.935.63a7.877 7.877 0 00-2.848 1.854A7.877 7.877 0 00-.631 5.332c-.296.733-.486 1.57-.552 2.794C-.078 9.352-.065 9.793-.065 13.414c0 3.622.013 4.063.078 5.289.066 1.224.256 2.061.552 2.794a7.877 7.877 0 001.854 2.848 7.877 7.877 0 002.848 1.854c.733.296 1.57.486 2.794.552 1.226.065 1.667.078 5.289.078 3.622 0 4.063-.013 5.289-.078 1.224-.066 2.061-.256 2.794-.552a7.877 7.877 0 002.848-1.854 7.877 7.877 0 001.854-2.848c.296-.733.486-1.57.552-2.794.065-1.226.078-1.667.078-5.289 0-3.622-.013-4.063-.078-5.289-.066-1.224-.256-2.061-.552-2.794A7.877 7.877 0 0019.732.483 7.877 7.877 0 0016.884-.631C16.151-.927 15.314-1.117 14.09-1.183 12.864-1.248 12.423-1.235 8.801-1.235 5.179-1.235 4.738-1.222 3.512-1.157 2.288-1.091 1.451-.901.718-.605A7.877 7.877 0 00-2.13 1.249 7.877 7.877 0 00-3.984 4.097c-.296.733-.486 1.57-.552 2.794C-4.601 8.117-4.614 8.558-4.614 12.18c0 3.622.013 4.063.078 5.289.066 1.224.256 2.061.552 2.794a7.877 7.877 0 001.854 2.848 7.877 7.877 0 002.848 1.854c.733.296 1.57.486 2.794.552 1.226.065 1.667.078 5.289.078z" clipRule="evenodd" />
          <path d="M12.017 2.892c-3.539 0-3.961.014-5.353.078-1.295.059-1.999.269-2.468.446a4.108 4.108 0 00-1.526.991 4.108 4.108 0 00-.991 1.526c-.177.469-.387 1.173-.446 2.468-.064 1.392-.078 1.814-.078 5.353s.014 3.961.078 5.353c.059 1.295.269 1.999.446 2.468a4.108 4.108 0 00.991 1.526 4.108 4.108 0 001.526.991c.469.177 1.173.387 2.468.446 1.392.064 1.814.078 5.353.078s3.961-.014 5.353-.078c1.295-.059 1.999-.269 2.468-.446a4.108 4.108 0 001.526-.991 4.108 4.108 0 00.991-1.526c.177-.469.387-1.173.446-2.468.064-1.392.078-1.814.078-5.353s-.014-3.961-.078-5.353c-.059-1.295-.269-1.999-.446-2.468a4.108 4.108 0 00-.991-1.526 4.108 4.108 0 00-1.526-.991c-.469-.177-1.173-.387-2.468-.446-1.392-.064-1.814-.078-5.353-.078zm0 1.622c3.474 0 3.873.014 5.239.077 1.264.058 1.95.269 2.407.446.605.235 1.037.517 1.491.971.454.454.736.886.971 1.491.177.457.388 1.143.446 2.407.063 1.366.077 1.765.077 5.239s-.014 3.873-.077 5.239c-.058 1.264-.269 1.95-.446 2.407-.235.605-.517 1.037-.971 1.491-.454.454-.886.736-1.491.971-.457.177-1.143.388-2.407.446-1.366.063-1.765.077-5.239.077s-3.873-.014-5.239-.077c-1.264-.058-1.95-.269-2.407-.446a4.014 4.014 0 01-1.491-.971 4.014 4.014 0 01-.971-1.491c-.177-.457-.388-1.143-.446-2.407-.063-1.366-.077-1.765-.077-5.239s.014-3.873.077-5.239c.058-1.264.269-1.95.446-2.407.235-.605.517-1.037.971-1.491.454-.454.886-.736 1.491-.971.457-.177 1.143-.388 2.407-.446 1.366-.063 1.765-.077 5.239-.077z" />
          <circle cx="12.017" cy="12.017" r="3.108" />
          <circle cx="17.672" cy="6.362" r="1.027" />
        </svg>
      )
    },
    {
      name: 'LinkedIn',
      href: '#',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
      )
    }
  ];

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main footer content */}
        <div className="py-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Company info */}
          <div className="lg:col-span-1">
            <h3 className="text-2xl font-bold text-white mb-4">AgentShop</h3>
            <p className="text-gray-300 text-sm mb-4">
              Your premier destination for digital products and services. 
              Quality, innovation, and customer satisfaction are our priorities.
            </p>
            <div className="flex space-x-4">
              {socialLinks.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className="text-gray-400 hover:text-white transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="sr-only">{item.name}</span>
                  {item.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Footer sections */}
          {footerSections.map((section) => (
            <div key={section.title}>
              <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                {section.title}
              </h4>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <NavLink
                      to={link.href}
                      className="text-gray-300 hover:text-white transition-colors text-sm"
                    >
                      {link.name}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Newsletter signup */}
        <div className="border-t border-gray-700 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="mb-4 md:mb-0">
              <h4 className="text-lg font-semibold text-white mb-2">Stay updated</h4>
              <p className="text-gray-300 text-sm">
                Subscribe to our newsletter for the latest products and offers.
              </p>
            </div>
            <form className="flex w-full md:w-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 md:w-64 px-4 py-2 bg-gray-800 border border-gray-600 rounded-l-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-emerald-600 text-white rounded-r-md hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-700 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between text-sm text-gray-400">
            <div className="mb-4 md:mb-0">
              <p>&copy; 2024 AgentShop. All rights reserved.</p>
            </div>
            <div className="flex space-x-6">
              <NavLink to="/privacy" className="hover:text-white transition-colors">
                Privacy
              </NavLink>
              <NavLink to="/terms" className="hover:text-white transition-colors">
                Terms
              </NavLink>
              <NavLink to="/cookies" className="hover:text-white transition-colors">
                Cookies
              </NavLink>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};