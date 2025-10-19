export default function HeroSplit(props:any){
  return (
    <section className="py-16">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-8 px-6">
        <div>
          <h1 className="text-4xl font-bold">{props.title}</h1>
          <p className="mt-4 text-lg opacity-80">{props.subtitle}</p>
        </div>
        <div>{/* image slot */}</div>
      </div>
    </section>
  );
}
