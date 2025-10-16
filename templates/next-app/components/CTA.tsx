export default function CTA({label="Get Started",href="#"}) {export default function CTA({label="Get Started",href="#"}) {

  return (  return (

    <section className="py-12 text-center">    <section className="py-12 text-center">

      <a href={href} className="inline-block px-6 py-3 rounded-xl border">{label}</a>      <a href={href} className="inline-block px-6 py-3 rounded-xl border">{label}</a>

    </section>    </section>

  );  );

}}

