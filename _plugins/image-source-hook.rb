# frozen_string_literal: true

module DraftsAndDragons
  module ImageSourceHook
    module_function

    def apply(document)
      image = document.data["image"]
      return unless image.is_a?(Hash)

      drive_id = image["drive_id"]
      source = image["source"] || image["path"] || image["image"]

      drive_id = extract_drive_id(source) if blank?(drive_id)
      return if blank?(drive_id)

      image["drive_id"] = drive_id
      image["path"] = direct_image_url(drive_id)
      image["source"] ||= share_url(drive_id)
    end

    def extract_drive_id(value)
      return nil unless value.is_a?(String)

      if value.include?("/file/d/")
        value.split("/file/d/", 2).last.to_s.split("/", 2).first
      elsif value.include?("id=")
        value.split("id=", 2).last.to_s.split("&", 2).first
      end
    end

    def direct_image_url(drive_id)
      "https://drive.google.com/uc?export=view&id=#{drive_id}"
    end

    def share_url(drive_id)
      "https://drive.google.com/file/d/#{drive_id}/view"
    end

    def blank?(value)
      value.nil? || value.to_s.strip.empty?
    end
  end
end

Jekyll::Hooks.register :posts, :post_init do |post|
  DraftsAndDragons::ImageSourceHook.apply(post)
end

Jekyll::Hooks.register :documents, :post_init do |document|
  next unless document.respond_to?(:collection) && document.collection.label == "drafts"

  DraftsAndDragons::ImageSourceHook.apply(document)
end

Jekyll::Hooks.register :site, :post_read do |site|
  site.posts.docs.each do |post|
    DraftsAndDragons::ImageSourceHook.apply(post)
  end

  drafts = site.collections["drafts"]
  next unless drafts

  drafts.docs.each do |document|
    DraftsAndDragons::ImageSourceHook.apply(document)
  end
end
