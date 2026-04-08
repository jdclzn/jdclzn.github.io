# frozen_string_literal: true

require "open3"
require "pathname"

module DraftsAndDragons
  module PostsLastmodHook
    module_function

    def apply(document)
      return if manual_lastmod?(document)

      repo_root = repository_root(document)
      return if blank?(repo_root)

      relative_path = repository_relative_path(document, repo_root)
      return if blank?(relative_path)

      # Preserve the publish date as the primary timestamp until the file has
      # been updated after its initial commit.
      return unless commit_count(repo_root, relative_path) > 1

      last_modified_at = git(repo_root, "log", "-1", "--format=%cI", "--", relative_path)
      return if blank?(last_modified_at)

      document.data["last_modified_at"] = last_modified_at
    end

    def manual_lastmod?(document)
      !blank?(document.data["last_modified_at"])
    end

    def repository_root(document)
      git(site_source(document), "rev-parse", "--show-toplevel")
    end

    def repository_relative_path(document, repo_root)
      absolute_path = Pathname.new(document.path)
      absolute_path = Pathname.new(File.expand_path(absolute_path.to_s, site_source(document))) unless absolute_path.absolute?

      absolute_path.relative_path_from(Pathname.new(repo_root)).to_s
    rescue ArgumentError
      nil
    end

    def site_source(document)
      return document.site.source if document.respond_to?(:site) && document.site.respond_to?(:source)

      Dir.pwd
    end

    def commit_count(repo_root, relative_path)
      git(repo_root, "rev-list", "--count", "HEAD", "--", relative_path).to_i
    end

    def git(chdir, *args)
      stdout, status = Open3.capture2("git", *args, chdir: chdir)
      return nil unless status.success?

      stdout.strip
    rescue StandardError
      nil
    end

    def blank?(value)
      value.nil? || value.to_s.strip.empty?
    end
  end
end

Jekyll::Hooks.register :posts, :post_init do |post|
  DraftsAndDragons::PostsLastmodHook.apply(post)
end

Jekyll::Hooks.register :documents, :post_init do |document|
  next unless document.respond_to?(:collection) && document.collection.label == "drafts"

  DraftsAndDragons::PostsLastmodHook.apply(document)
end
