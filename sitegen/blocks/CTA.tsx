export default function CTA({label="Get Started",href="#"}) {
  return (
    <section className="py-12 text-center">
      <a href={href} className="inline-block px-6 py-3 rounded-xl border">{label}</a>
    </section>
  );
}
