Gem::Specification.new do |spec|
  spec.name = "jekyll-compose-time-compat"
  spec.version = "0.1.0"
  spec.summary = "Compatibility patch for jekyll-compose timestamp front matter."
  spec.authors = ["Jovanie Daclizon"]
  spec.files = Dir["lib/**/*.rb"]
  spec.require_paths = ["lib"]

  spec.add_dependency "jekyll-compose", "~> 0.12.0"
end
