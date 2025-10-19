export default function FeaturesGrid({items=[]}:{items:any[]}) {
  return (
    <section className="py-16">
      <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6 px-6">
        {items.map((x,i)=>(
          <div key={i} className="p-6 border rounded-xl">
            <h3 className="font-semibold">{x.title}</h3>
            <p className="text-sm mt-2 opacity-80">{x.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
